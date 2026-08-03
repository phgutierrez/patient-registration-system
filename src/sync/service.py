"""Publicação e consumo de eventos criptografados no compartilhamento."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from src.extensions import db
from src.models.sync import (
    SyncAppliedEvent,
    SyncAuditRevision,
    SyncDeviceState,
    SyncOutbox,
)

from .adapters import DeferredDependency, adapters_by_name, decode_value, encode_value
from .clock import HybridLogicalClock
from .crypto import SyncCryptoError, decrypt_json, encrypt_json
from .runtime import SyncRuntime, initialize_runtime


logger = logging.getLogger(__name__)


def _canonical_json(value: dict) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')


class SyncService:
    def __init__(self):
        self.app = None
        self.runtime: SyncRuntime | None = None
        self.clock = HybridLogicalClock('local')
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._run_lock = threading.Lock()
        self._status_lock = threading.Lock()
        self._last_error: str | None = None
        self._last_success_at: datetime | None = None

    def configure(self, app) -> SyncRuntime:
        self.app = app
        self.runtime = initialize_runtime(app.config)
        self.clock = HybridLogicalClock(self.runtime.device_uuid)
        app.extensions['offline_sync'] = self
        if (
            self.runtime.ready
            and app.config.get('SYNC_START_WORKER', True)
            and not app.config.get('TESTING', False)
        ):
            self.start()
        return self.runtime

    def next_event_identity(self) -> tuple[str, str]:
        return self.clock.next()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._worker,
            name='patient-registration-sync',
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout)

    def wake(self) -> None:
        self._wake.set()

    def pair(self, recovery_key: str) -> None:
        if not self.runtime:
            raise RuntimeError('Sincronização ainda não inicializada.')
        self.runtime.pair(recovery_key)
        self.clock = HybridLogicalClock(self.runtime.device_uuid)

    def enqueue_baseline(self) -> int:
        """Coloca registros legados ainda sem versão na outbox inicial.

        O método é idempotente: entidades que já possuem qualquer versão de
        campo foram criadas localmente pelos hooks ou recebidas da rede.
        """
        if not self.app or not self.runtime or not self.runtime.ready:
            return 0
        from src.models.sync import new_sync_uuid

        created = 0
        db.session.info['sync_applying'] = True
        try:
            for adapter in adapters_by_name().values():
                for obj in adapter.model.query.all():
                    if obj.get_sync_field_versions():
                        continue
                    if not obj.sync_uuid:
                        obj.sync_uuid = new_sync_uuid()
                    event_order, event_uuid = self.next_event_identity()
                    selected = set(adapter.event_fields)
                    changes = adapter.export(obj, selected)
                    changes['_deleted'] = bool(obj.sync_deleted)
                    versions = {name: event_order for name in changes}
                    obj.set_sync_field_versions(versions)
                    obj.sync_updated_at = datetime.utcnow()
                    payload = {
                        'event_uuid': event_uuid,
                        'event_order': event_order,
                        'entity_type': adapter.entity_type,
                        'entity_uuid': obj.sync_uuid,
                        'changes': changes,
                        'field_versions': versions,
                    }
                    db.session.add(SyncOutbox(
                        event_uuid=event_uuid,
                        event_order=event_order,
                        entity_type=adapter.entity_type,
                        entity_uuid=obj.sync_uuid,
                        payload_json=json.dumps(
                            payload, ensure_ascii=False, sort_keys=True,
                            separators=(',', ':'),
                        ),
                    ))
                    created += 1
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        finally:
            db.session.info.pop('sync_applying', None)
        if created:
            logger.info('Baseline de sincronização criado com %s entidade(s).', created)
            self.wake()
        return created
    def _worker(self) -> None:
        interval = max(
            2,
            int(self.app.config.get('SYNC_INTERVAL_SECONDS', 5)),
        )
        while not self._stop.is_set():
            try:
                self.sync_once()
            except Exception:
                logger.exception('Ciclo de sincronização falhou.')
            self._wake.wait(interval)
            self._wake.clear()

    def sync_once(self) -> dict:
        if not self.app or not self.runtime or not self.runtime.ready:
            return self.status()
        if not self._run_lock.acquire(blocking=False):
            return self.status()
        try:
            with self.app.app_context():
                self._publish_pending()
                self._consume_available()
                self._maybe_write_checkpoint()
                with self._status_lock:
                    self._last_success_at = datetime.utcnow()
                    self._last_error = None
        except Exception as exc:
            with self._status_lock:
                self._last_error = str(exc)[:500]
            raise
        finally:
            self._run_lock.release()
        return self.status()

    def _checkpoint_payload(self) -> dict:
        entities = []
        for adapter in adapters_by_name().values():
            for obj in adapter.model.query.order_by(adapter.model.id).all():
                selected = set(adapter.event_fields)
                changes = adapter.export(obj, selected)
                changes['_deleted'] = bool(obj.sync_deleted)
                versions = obj.get_sync_field_versions()
                event_order = max(versions.values(), default=self.clock.next()[0])
                synthetic_uuid = str(uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f'{self.runtime.deployment_id}:{adapter.entity_type}:{obj.sync_uuid}:checkpoint',
                ))
                entities.append({
                    'event_uuid': synthetic_uuid,
                    'event_order': event_order,
                    'entity_type': adapter.entity_type,
                    'entity_uuid': obj.sync_uuid,
                    'changes': changes,
                    'field_versions': {
                        name: versions.get(name, event_order) for name in changes
                    },
                })
        return {
            'format': 1,
            'deployment_id': self.runtime.deployment_id,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'entities': entities,
        }

    def _maybe_write_checkpoint(self) -> None:
        assert self.runtime and self.runtime.shared_root and self.runtime.master_key
        checkpoint_dir = self.runtime.shared_root / 'checkpoints'
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        latest = max(checkpoint_dir.glob('*.checkpoint'), key=lambda p: p.stat().st_mtime, default=None)
        if latest and time.time() - latest.stat().st_mtime < 3600:
            return
        lock = checkpoint_dir / '.checkpoint-lock'
        try:
            lock.mkdir()
        except FileExistsError:
            return
        try:
            latest = max(checkpoint_dir.glob('*.checkpoint'), key=lambda p: p.stat().st_mtime, default=None)
            if latest and time.time() - latest.stat().st_mtime < 3600:
                return
            payload = self._checkpoint_payload()
            header = {
                'format': 1,
                'deployment_id': self.runtime.deployment_id,
                'source_device_uuid': self.runtime.device_uuid,
                'kind': 'checkpoint',
            }
            outer = {
                'header': header,
                'encrypted': encrypt_json(self.runtime.master_key, payload, header),
            }
            stamp = datetime.utcnow().strftime('%Y%m%dT%H%M%S%fZ')
            final_path = checkpoint_dir / (
                f'{stamp}-{self.runtime.device_uuid}.checkpoint'
            )
            temporary = checkpoint_dir / f'.{uuid.uuid4().hex}.tmp'
            encoded = _canonical_json(outer)
            with temporary.open('wb') as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, final_path)
            logger.info('Checkpoint criptografado criado com %s entidade(s).', len(payload['entities']))
        finally:
            try:
                lock.rmdir()
            except OSError:
                pass

    def restore_latest_checkpoint(self) -> int:
        if not self.runtime or not self.runtime.ready:
            return 0
        checkpoint_dir = self.runtime.shared_root / 'checkpoints'
        if not checkpoint_dir.is_dir():
            return 0
        candidates = sorted(checkpoint_dir.glob('*.checkpoint'), reverse=True)
        if not candidates:
            return 0
        path = candidates[0]
        try:
            outer = json.loads(path.read_text(encoding='utf-8'))
            header = outer['header']
            if header.get('deployment_id') != self.runtime.deployment_id:
                raise RuntimeError('Checkpoint pertence a outra implantação.')
            payload = decrypt_json(self.runtime.master_key, outer['encrypted'], header)
        except (OSError, ValueError, KeyError, SyncCryptoError) as exc:
            raise RuntimeError('Checkpoint ausente, truncado ou adulterado.') from exc
        entities = payload.get('entities')
        if not isinstance(entities, list):
            raise RuntimeError('Checkpoint não contém uma lista de entidades válida.')
        applied = 0
        for sequence, entity in enumerate(entities, start=1):
            self._apply_payload(entity, 'checkpoint', sequence)
            db.session.commit()
            applied += 1
        logger.info('Checkpoint restaurado com %s entidade(s).', applied)
        return applied
    def status(self) -> dict:
        pending = None
        if self.app:
            try:
                with self.app.app_context():
                    pending = SyncOutbox.query.filter_by(published_at=None).count()
            except Exception:
                pending = None
        runtime = self.runtime
        with self._status_lock:
            return {
                'enabled': bool(runtime and runtime.enabled),
                'ready': bool(runtime and runtime.ready),
                'pairing_required': bool(runtime and runtime.pairing_required),
                'pending': pending,
                'last_error': self._last_error or (runtime.error if runtime else None),
                'last_success_at': (
                    self._last_success_at.isoformat() + 'Z'
                    if self._last_success_at else None
                ),
                'device_uuid': runtime.device_uuid if runtime else None,
            }

    def _device_state(self, device_uuid: str) -> SyncDeviceState:
        state = SyncDeviceState.query.filter_by(device_uuid=device_uuid).first()
        if state is None:
            state = SyncDeviceState(device_uuid=device_uuid)
            db.session.add(state)
            db.session.flush()
        return state

    def _publish_pending(self) -> None:
        assert self.runtime and self.runtime.shared_root and self.runtime.master_key
        event_dir = (
            self.runtime.shared_root / 'events' / self.runtime.device_uuid
        )
        event_dir.mkdir(parents=True, exist_ok=True)
        pending = (
            SyncOutbox.query
            .filter_by(published_at=None)
            .order_by(SyncOutbox.id.asc())
            .all()
        )
        for row in pending:
            state = self._device_state(self.runtime.device_uuid)
            sequence = state.last_published_sequence + 1
            header = {
                'format': 1,
                'deployment_id': self.runtime.deployment_id,
                'source_device_uuid': self.runtime.device_uuid,
                'sequence': sequence,
                'previous_hash': state.last_published_hash,
                'event_uuid': row.event_uuid,
            }
            payload = json.loads(row.payload_json)
            outer = {
                'header': header,
                'encrypted': encrypt_json(
                    self.runtime.master_key, payload, header
                ),
            }
            encoded = _canonical_json(outer)
            current_hash = hashlib.sha256(encoded).hexdigest()
            final_path = event_dir / f'{sequence:012d}-{row.event_uuid}.event'

            if final_path.exists():
                existing = final_path.read_bytes()
                if existing != encoded:
                    raise RuntimeError(
                        f'Colisão de sequência no dispositivo {self.runtime.device_uuid}.'
                    )
                current_hash = hashlib.sha256(existing).hexdigest()
            else:
                temporary = event_dir / (
                    f'.{sequence:012d}-{uuid.uuid4().hex}.tmp'
                )
                with temporary.open('wb') as handle:
                    handle.write(encoded)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, final_path)

            state.last_published_sequence = sequence
            state.last_published_hash = current_hash
            state.last_seen_at = datetime.utcnow()
            row.published_at = datetime.utcnow()
            row.publish_attempts += 1
            row.last_error = None
            db.session.commit()

    def _consume_available(self) -> None:
        assert self.runtime and self.runtime.shared_root
        events_root = self.runtime.shared_root / 'events'
        if not events_root.exists():
            return
        made_progress = True
        consumed = 0
        max_events = max(
            100,
            int(self.app.config.get('SYNC_MAX_EVENTS_PER_CYCLE', 5000)),
        )
        while made_progress and consumed < max_events:
            made_progress = False
            for source_dir in sorted(
                (path for path in events_root.iterdir() if path.is_dir()),
                key=lambda path: path.name,
            ):
                if self._consume_source(source_dir.name, source_dir):
                    made_progress = True
                    consumed += 1
                    if consumed >= max_events:
                        break
        if consumed >= max_events:
            logger.info(
                'Limite de %s eventos atingido; o restante seguirá no próximo ciclo.',
                max_events,
            )

    def _consume_source(self, source_uuid: str, source_dir: Path) -> bool:
        state = self._device_state(source_uuid)
        sequence = state.last_consumed_sequence + 1
        candidates = sorted(source_dir.glob(f'{sequence:012d}-*.event'))
        if not candidates:
            later_sequences = []
            for later_path in source_dir.glob('*.event'):
                try:
                    later_sequences.append(int(later_path.name.split('-', 1)[0]))
                except (ValueError, IndexError):
                    raise RuntimeError(
                        f'Nome de evento inválido em {source_uuid}: {later_path.name}'
                    )
            if any(value > sequence for value in later_sequences):
                raise RuntimeError(
                    f'Sequência {sequence} ausente ou removida em {source_uuid}.'
                )
            return False
        if len(candidates) != 1:
            raise RuntimeError(
                f'Mais de um evento ocupa a sequência {sequence} de {source_uuid}.'
            )

        path = candidates[0]
        encoded = path.read_bytes()
        current_hash = hashlib.sha256(encoded).hexdigest()
        try:
            outer = json.loads(encoded.decode('utf-8'))
            header = outer['header']
        except (ValueError, KeyError, TypeError) as exc:
            raise RuntimeError(f'Evento inválido: {path.name}') from exc
        expected = {
            'deployment_id': self.runtime.deployment_id,
            'source_device_uuid': source_uuid,
            'sequence': sequence,
            'previous_hash': state.last_consumed_hash,
        }
        for key, value in expected.items():
            if header.get(key) != value:
                raise RuntimeError(
                    f'Cadeia de eventos inválida em {source_uuid}, sequência {sequence}.'
                )
        try:
            payload = decrypt_json(
                self.runtime.master_key, outer['encrypted'], header
            )
        except (KeyError, SyncCryptoError) as exc:
            raise RuntimeError(f'Falha de integridade em {path.name}: {exc}') from exc

        self.clock.observe(payload.get('event_order', ''))
        try:
            self._apply_payload(payload, source_uuid, sequence)
        except DeferredDependency:
            db.session.rollback()
            return False

        state = self._device_state(source_uuid)
        state.last_consumed_sequence = sequence
        state.last_consumed_hash = current_hash
        state.last_seen_at = datetime.utcnow()
        state.last_error = None
        db.session.commit()
        return True

    def _apply_payload(self, payload: dict, source_uuid: str, sequence: int) -> None:
        event_uuid = str(payload['event_uuid'])
        if SyncAppliedEvent.query.filter_by(event_uuid=event_uuid).first():
            return
        adapter = adapters_by_name().get(payload.get('entity_type'))
        if adapter is None:
            raise RuntimeError(
                f"Tipo de entidade desconhecido: {payload.get('entity_type')}"
            )
        changes = payload.get('changes')
        incoming_versions = payload.get('field_versions')
        if not isinstance(changes, dict) or not isinstance(incoming_versions, dict):
            raise RuntimeError('Evento sem alterações ou versões válidas.')

        db.session.info['sync_applying'] = True
        try:
            obj, _ = adapter.find_or_create(str(payload['entity_uuid']), changes)
            versions = obj.get_sync_field_versions()
            for field_name, encoded_value in changes.items():
                incoming_order = str(
                    incoming_versions.get(field_name) or payload['event_order']
                )
                previous_order = versions.get(field_name)
                accepted = previous_order is None or incoming_order > previous_order
                previous_value = None
                if field_name == '_deleted':
                    previous_value = bool(obj.sync_deleted)
                elif field_name in adapter._reference_by_event:
                    reference = adapter._reference_by_event[field_name]
                    target = getattr(obj, reference.relationship, None)
                    previous_value = getattr(target, 'sync_uuid', None)
                elif field_name in adapter.fields:
                    previous_value = getattr(obj, field_name)

                if accepted:
                    resolved_value = self._prepare_unique_value(
                        adapter.entity_type,
                        obj,
                        field_name,
                        decode_value(encoded_value),
                        incoming_order,
                    )
                    if field_name == '_deleted':
                        obj.sync_deleted = bool(encoded_value)
                    elif field_name in adapter._reference_by_event:
                        adapter.apply_reference(obj, field_name, encoded_value)
                    elif field_name in adapter.fields:
                        setattr(obj, field_name, resolved_value)
                    versions[field_name] = incoming_order

                if previous_order and previous_value != decode_value(encoded_value):
                    db.session.add(SyncAuditRevision(
                        event_uuid=event_uuid,
                        entity_type=adapter.entity_type,
                        entity_uuid=obj.sync_uuid,
                        field_name=field_name,
                        previous_value_json=json.dumps(
                            encode_value(previous_value), ensure_ascii=False
                        ),
                        incoming_value_json=json.dumps(
                            encoded_value, ensure_ascii=False
                        ),
                        previous_order=previous_order,
                        incoming_order=incoming_order,
                        accepted=accepted,
                    ))

            obj.set_sync_field_versions(versions)
            obj.sync_updated_at = datetime.utcnow()
            db.session.flush()
            if adapter.entity_type == 'patient':
                self._canonicalize_patient(obj, payload['event_order'])
            db.session.add(SyncAppliedEvent(
                event_uuid=event_uuid,
                source_device_uuid=source_uuid,
                source_sequence=sequence,
                event_order=str(payload['event_order']),
            ))
            db.session.flush()
        except IntegrityError as exc:
            db.session.rollback()
            constraint = str(getattr(exc, 'orig', exc)).split('[SQL:', 1)[0][:240]
            logger.warning(
                'Restrição local ao aplicar sync: entidade=%s motivo=%s',
                adapter.entity_type,
                constraint,
            )
            raise RuntimeError(
                f'Não foi possível restaurar {adapter.entity_type}: {constraint}'
            ) from exc
        finally:
            db.session.info.pop('sync_applying', None)

    def _prepare_unique_value(
        self,
        entity_type: str,
        obj,
        field_name: str,
        value,
        incoming_order: str,
    ):
        if entity_type != 'user' or not value:
            return value
        from src.models.user import User

        if field_name not in {'username', 'cns', 'crm'}:
            return value
        other = User.query.filter(
            getattr(User, field_name) == value,
            User.sync_uuid != obj.sync_uuid,
        ).first()
        if other is None:
            return value
        other_versions = other.get_sync_field_versions()
        if other_versions.get(field_name, '') > incoming_order:
            if field_name == 'username':
                suffix = obj.sync_uuid.replace('-', '')[:10]
                return f'conflito-{suffix}'
            return None
        if field_name == 'username':
            suffix = other.sync_uuid.replace('-', '')[:10]
            other.username = f'conflito-{suffix}'
        else:
            setattr(other, field_name, None)
        other_versions[field_name] = incoming_order
        other.set_sync_field_versions(other_versions)
        return value

    def _canonicalize_patient(self, patient, event_order: str) -> None:
        if not patient.prontuario or patient.sync_deleted:
            return
        from src.models.patient import Patient

        other = Patient.query.filter(
            Patient.id != patient.id,
            Patient.specialty_id == patient.specialty_id,
            Patient.prontuario == patient.prontuario,
            Patient.sync_deleted.is_(False),
        ).first()
        if other is None:
            return
        other_versions = other.get_sync_field_versions()
        patient_versions = patient.get_sync_field_versions()
        canonical_order = max(
            event_order,
            other_versions.get('prontuario', ''),
            patient_versions.get('prontuario', ''),
        )
        if other_versions.get('prontuario', '') > patient_versions.get(
            'prontuario', event_order
        ):
            winner, loser = other, patient
        else:
            winner, loser = patient, other

        loser.superseded_by_uuid = winner.sync_uuid
        loser.sync_deleted = True
        loser_versions = loser.get_sync_field_versions()
        loser_versions['superseded_by_uuid'] = canonical_order
        loser_versions['_deleted'] = canonical_order
        loser.set_sync_field_versions(loser_versions)
        loser.sync_updated_at = datetime.utcnow()

        # Limpa uma referência antiga caso o registro vencedor tenha sido
        # comparado anteriormente com outra cópia. O mesmo order em todas as
        # estações mantém a decisão convergente.
        winner.superseded_by_uuid = None
        winner_versions = winner.get_sync_field_versions()
        winner_versions['superseded_by_uuid'] = canonical_order
        winner.set_sync_field_versions(winner_versions)
        winner.sync_updated_at = datetime.utcnow()


sync_service = SyncService()
