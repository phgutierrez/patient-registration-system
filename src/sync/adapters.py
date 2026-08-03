"""Mapeamentos explícitos entre modelos locais e eventos portáveis."""
from __future__ import annotations

import base64
import secrets
from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy import inspect

from src.extensions import db


class DeferredDependency(RuntimeError):
    pass


def encode_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return {'$type': 'datetime', 'value': value.isoformat()}
    if isinstance(value, date):
        return {'$type': 'date', 'value': value.isoformat()}
    if isinstance(value, time):
        return {'$type': 'time', 'value': value.isoformat()}
    if isinstance(value, Decimal):
        return {'$type': 'decimal', 'value': str(value)}
    if isinstance(value, bytes):
        return {'$type': 'bytes', 'value': base64.b64encode(value).decode('ascii')}
    return value


def decode_value(value: Any) -> Any:
    if not isinstance(value, dict) or '$type' not in value:
        return value
    kind = value.get('$type')
    raw = value.get('value')
    if kind == 'datetime':
        return datetime.fromisoformat(raw)
    if kind == 'date':
        return date.fromisoformat(raw)
    if kind == 'time':
        return time.fromisoformat(raw)
    if kind == 'decimal':
        return Decimal(raw)
    if kind == 'bytes':
        return base64.b64decode(raw)
    return value


@dataclass(frozen=True)
class Reference:
    event_field: str
    local_fk: str
    relationship: str
    target_type: str
    nullable: bool = True


@dataclass
class SyncAdapter:
    entity_type: str
    model: type
    fields: tuple[str, ...]
    references: tuple[Reference, ...] = ()
    factory: Callable[[str], object] | None = None
    natural_key: str | None = None
    _reference_by_event: dict[str, Reference] = field(init=False, default_factory=dict)

    def __post_init__(self):
        self._reference_by_event = {
            reference.event_field: reference for reference in self.references
        }

    @property
    def event_fields(self) -> tuple[str, ...]:
        return self.fields + tuple(self._reference_by_event)

    def changed_fields(self, obj, *, is_new: bool) -> set[str]:
        if is_new:
            return set(self.event_fields)
        state = inspect(obj)
        changed = {
            name for name in self.fields
            if name in state.attrs and state.attrs[name].history.has_changes()
        }
        for reference in self.references:
            if (
                reference.local_fk in state.attrs
                and state.attrs[reference.local_fk].history.has_changes()
            ):
                changed.add(reference.event_field)
        return changed

    def export(self, obj, selected: set[str]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name in self.fields:
            if name in selected:
                result[name] = encode_value(getattr(obj, name))
        for reference in self.references:
            if reference.event_field not in selected:
                continue
            target = getattr(obj, reference.relationship, None)
            result[reference.event_field] = (
                getattr(target, 'sync_uuid', None) if target is not None else None
            )
        return result

    def find_or_create(self, entity_uuid: str, changes: dict):
        existing = self.model.query.filter_by(sync_uuid=entity_uuid).first()
        if existing is not None:
            return existing, False
        if self.natural_key and changes.get(self.natural_key):
            candidate = self.model.query.filter_by(
                **{self.natural_key: decode_value(changes[self.natural_key])}
            ).first()
            if (
                candidate is not None
                and not candidate.get_sync_field_versions()
            ):
                candidate.sync_uuid = entity_uuid
                return candidate, False
        obj = self.factory(entity_uuid) if self.factory else self.model()
        obj.sync_uuid = entity_uuid
        db.session.add(obj)
        return obj, True

    def apply_reference(self, obj, name: str, value: Any) -> None:
        reference = self._reference_by_event[name]
        if value is None:
            if not reference.nullable:
                raise DeferredDependency(f'Referência obrigatória ausente: {name}')
            setattr(obj, reference.local_fk, None)
            return
        target_adapter = adapters_by_name()[reference.target_type]
        # O objeto atual ainda pode não ter sua FK obrigatória. Uma query normal
        # faria autoflush e tentaria inseri-lo incompleto antes de encontrarmos o
        # alvo, causando NOT NULL em specialty_id/patient_id.
        with db.session.no_autoflush:
            target = target_adapter.model.query.filter_by(
                sync_uuid=str(value)
            ).first()
        if target is None:
            raise DeferredDependency(
                f'{reference.target_type} {value} ainda não foi sincronizado.'
            )
        if target.id is None:
            raise DeferredDependency(
                f'{reference.target_type} {value} ainda não foi persistido.'
            )
        setattr(obj, reference.local_fk, target.id)


_ADAPTERS: dict[str, SyncAdapter] | None = None


def _user_factory(entity_uuid: str):
    from src.models.user import User

    suffix = entity_uuid.replace('-', '')[:10]
    return User(
        username=f'sync-{suffix}',
        password=f'{secrets.randbelow(1_000_000):06d}',
        full_name='Usuário sincronizado',
        role='solicitante',
    )


def adapters_by_name() -> dict[str, SyncAdapter]:
    global _ADAPTERS
    if _ADAPTERS is not None:
        return _ADAPTERS

    from src.models.calendar_event_status import CalendarEventStatus
    from src.models.patient import Patient
    from src.models.specialty import Specialty, SpecialtyProcedure, SpecialtySettings
    from src.models.surgery_request import SurgeryRequest
    from src.models.sync import DocumentTemplateArchive, GeneratedDocumentSnapshot
    from src.models.user import User

    adapters = [
        SyncAdapter(
            'specialty', Specialty,
            ('slug', 'name', 'is_active', 'created_at', 'updated_at'),
            natural_key='slug',
        ),
        SyncAdapter(
            'specialty_settings', SpecialtySettings,
            ('agenda_url', 'forms_url', 'created_at', 'updated_at'),
            (Reference('specialty_uuid', 'specialty_id', 'specialty', 'specialty', False),),
        ),
        SyncAdapter(
            'specialty_procedure', SpecialtyProcedure,
            (
                'descricao', 'codigo_sus', 'is_active', 'sort_order',
                'created_at', 'updated_at',
            ),
            (Reference('specialty_uuid', 'specialty_id', 'specialty', 'specialty', False),),
        ),
        SyncAdapter(
            'user', User,
            (
                'username', 'password_hash', 'role', 'must_change_password',
                'full_name', 'cns', 'crm',
            ),
            (Reference('specialty_uuid', 'specialty_id', 'specialty', 'specialty'),),
            factory=_user_factory,
            natural_key='username',
        ),
        SyncAdapter(
            'patient', Patient,
            (
                'nome', 'prontuario', 'data_nascimento', 'sexo', 'nome_mae',
                'cns', 'cidade', 'endereco', 'estado', 'contato', 'diagnostico',
                'cid', 'created_at', 'updated_at', 'superseded_by_uuid',
            ),
            (Reference('specialty_uuid', 'specialty_id', 'specialty', 'specialty'),),
        ),
        SyncAdapter(
            'surgery_request', SurgeryRequest,
            (
                'peso', 'sinais_sintomas', 'condicoes_justificativa',
                'resultados_diagnosticos', 'procedimento_solicitado',
                'codigo_procedimento', 'tipo_cirurgia', 'data_cirurgia',
                'internar_antes', 'hora_cirurgia', 'assistente',
                'aparelhos_especiais', 'reserva_sangue', 'quantidade_sangue',
                'raio_x', 'reserva_uti', 'duracao_prevista',
                'evolucao_internacao', 'prescricao_internacao', 'exames_preop',
                'opme', 'status', 'scheduled_at', 'scheduled_event_id',
                'scheduled_event_link', 'calendar_status', 'scheduled_attempt_id',
                'scheduled_result_uncertain', 'created_at', 'updated_at',
            ),
            (
                Reference('patient_uuid', 'patient_id', 'patient', 'patient', False),
                Reference('specialty_uuid', 'specialty_id', 'specialty', 'specialty'),
                Reference(
                    'created_by_user_uuid', 'created_by_user_id',
                    'created_by_user', 'user',
                ),
            ),
        ),
        SyncAdapter(
            'calendar_event_status', CalendarEventStatus,
            (
                'event_uid', 'event_date', 'status', 'suspension_reason',
                'created_at', 'updated_at',
            ),
            (
                Reference(
                    'surgery_request_uuid', 'surgery_request_id',
                    'surgery_request', 'surgery_request',
                ),
            ),
            natural_key='event_uid',
        ),
        SyncAdapter(
            'document_template', DocumentTemplateArchive,
            (
                'document_type', 'template_id', 'template_sha256',
                'pdf_bytes', 'created_at',
            ),
            natural_key='template_sha256',
        ),        SyncAdapter(
            'generated_document', GeneratedDocumentSnapshot,
            (
                'document_type', 'revision', 'output_filename', 'payload_json',
                'template_id', 'template_sha256', 'renderer_version', 'created_at',
            ),
            (
                Reference(
                    'surgery_request_uuid', 'surgery_request_id',
                    'surgery_request', 'surgery_request', False,
                ),
                Reference(
                    'created_by_user_uuid', 'created_by_user_id',
                    'created_by_user', 'user',
                ),
            ),
        ),
    ]
    _ADAPTERS = {adapter.entity_type: adapter for adapter in adapters}
    return _ADAPTERS


def adapter_for_object(obj) -> SyncAdapter | None:
    for adapter in adapters_by_name().values():
        if isinstance(obj, adapter.model):
            return adapter
    return None
