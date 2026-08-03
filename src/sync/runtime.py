"""Descoberta da implantação, identidade da estação e chave de pareamento."""
from __future__ import annotations

import json
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .crypto import (
    LocalKeyStore,
    format_recovery_key,
    generate_master_key,
    parse_recovery_key,
    encrypt_json,
    decrypt_json,
    SyncCryptoError,
)


SYNC_SCHEMA_VERSION = 1


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp')
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, indent=2
    ).encode('utf-8')
    with temporary.open('wb') as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _load_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None


@dataclass
class SyncRuntime:
    enabled: bool
    local_root: Path
    shared_root: Path | None
    deployment_id: str
    device_uuid: str
    master_key: bytes | None
    pairing_required: bool = False
    recovery_key_once: str | None = None
    error: str | None = None
    initial_device: bool = False

    @property
    def ready(self) -> bool:
        return bool(
            self.enabled and self.shared_root and self.master_key
            and not self.pairing_required and not self.error
        )

    def pair(self, recovery_key: str) -> None:
        key = parse_recovery_key(recovery_key)
        verifier_path = self.shared_root / 'key-verifier.json'
        verifier = _load_json(verifier_path)
        if not verifier:
            raise SyncCryptoError(
                'A estação inicial ainda não publicou o verificador da chave.'
            )
        header = verifier.get('header') or {}
        if header.get('deployment_id') != self.deployment_id:
            raise SyncCryptoError('A chave pertence a outra implantação.')
        checked = decrypt_json(key, verifier.get('encrypted') or {}, header)
        if checked.get('deployment_id') != self.deployment_id:
            raise SyncCryptoError('Chave de recuperação incorreta.')
        LocalKeyStore(self.local_root / 'sync.key').save(key)
        self.master_key = key
        self.pairing_required = False
        self.error = None


def _device_uuid(local_root: Path) -> str:
    path = local_root / 'device.json'
    existing = _load_json(path)
    if existing and existing.get('device_uuid'):
        return str(existing['device_uuid'])
    value = str(uuid.uuid4())
    _atomic_json(path, {'device_uuid': value})
    return value


def initialize_runtime(config) -> SyncRuntime:
    enabled = bool(config.get('SYNC_ENABLED', False))
    configured_local = config.get('BASE_DIR') or config.get('INSTANCE_PATH')
    if not configured_local:
        protected = config.get('PROTECTED_PDF_DIR')
        configured_local = Path(protected).parent if protected else Path.cwd()
    local_root = Path(configured_local).resolve()
    configured_shared = str(config.get('SYNC_ROOT') or '').strip()
    shared_root = Path(configured_shared) if configured_shared else None
    local_manifest_path = local_root / 'deployment.local.json'
    local_manifest = _load_json(local_manifest_path)

    if not enabled:
        deployment_id = str(
            (local_manifest or {}).get('deployment_id') or uuid.uuid4()
        )
        return SyncRuntime(
            False, local_root, None, deployment_id,
            'sync-disabled', None,
        )

    if shared_root is None:
        return SyncRuntime(
            True, local_root, None,
            str((local_manifest or {}).get('deployment_id') or ''),
            _device_uuid(local_root), None,
            error='SYNC_ROOT não foi configurado.',
        )

    shared_manifest_path = shared_root / 'deployment.json'
    manifest = _load_json(shared_manifest_path)
    created = False
    if manifest is None:
        try:
            shared_root.mkdir(parents=True, exist_ok=True)
            lock = shared_root / '.initialize-lock'
            try:
                lock.mkdir()
                owns_lock = True
            except FileExistsError:
                owns_lock = False
            if owns_lock:
                try:
                    manifest = _load_json(shared_manifest_path)
                    if manifest is None:
                        manifest = {
                            'deployment_id': str(uuid.uuid4()),
                            'sync_schema_version': SYNC_SCHEMA_VERSION,
                            'created_at': datetime.now(timezone.utc).isoformat(),
                            'nonce': secrets.token_hex(16),
                            'key_initialized': True,
                            'key_owner_device_uuid': _device_uuid(local_root),
                        }
                        _atomic_json(shared_manifest_path, manifest)
                        created = True
                finally:
                    try:
                        lock.rmdir()
                    except OSError:
                        pass
            else:
                for _ in range(50):
                    import time
                    time.sleep(0.1)
                    manifest = _load_json(shared_manifest_path)
                    if manifest:
                        break
        except OSError as exc:
            if local_manifest:
                manifest = local_manifest
            else:
                return SyncRuntime(
                    True, local_root, shared_root, '',
                    _device_uuid(local_root), None,
                    error=f'Compartilhamento indisponível: {exc}',
                )

    if not manifest or not manifest.get('deployment_id'):
        return SyncRuntime(
            True, local_root, shared_root, '',
            _device_uuid(local_root), None,
            error='Manifesto de implantação ausente ou inválido.',
        )
    if int(manifest.get('sync_schema_version', 0)) > SYNC_SCHEMA_VERSION:
        return SyncRuntime(
            True, local_root, shared_root, str(manifest['deployment_id']),
            _device_uuid(local_root), None,
            error='Esta versão do aplicativo é antiga para os dados compartilhados.',
        )

    # O launcher pode criar o manifesto antes do serviço criptográfico. Apenas
    # uma estação reivindica a criação da chave inicial.
    if not manifest.get('key_initialized'):
        claim_lock = shared_root / '.key-initialize-lock'
        try:
            claim_lock.mkdir()
            owns_claim = True
        except FileExistsError:
            owns_claim = False
        if owns_claim:
            try:
                latest = _load_json(shared_manifest_path) or manifest
                if not latest.get('key_initialized'):
                    latest['key_initialized'] = True
                    latest['key_initialized_at'] = datetime.now(timezone.utc).isoformat()
                    latest['key_owner_device_uuid'] = _device_uuid(local_root)
                    _atomic_json(shared_manifest_path, latest)
                    manifest = latest
                    created = True
                else:
                    manifest = latest
            finally:
                try:
                    claim_lock.rmdir()
                except OSError:
                    pass
        else:
            for _ in range(50):
                import time
                time.sleep(0.1)
                latest = _load_json(shared_manifest_path)
                if latest and latest.get('key_initialized'):
                    manifest = latest
                    break
            if not manifest.get('key_initialized'):
                return SyncRuntime(
                    True, local_root, shared_root, str(manifest['deployment_id']),
                    _device_uuid(local_root), None,
                    error='A primeira estação não concluiu a criação da chave.',
                )

    _atomic_json(local_manifest_path, manifest)
    device_uuid = _device_uuid(local_root)
    initial_device = manifest.get('key_owner_device_uuid') == device_uuid
    key_store = LocalKeyStore(local_root / 'sync.key')
    recovery_once = None
    runtime_error = None
    if key_store.exists():
        key = key_store.load()
        pairing_required = False
        if not (local_root / 'recovery.confirmed').exists():
            if initial_device:
                recovery_once = format_recovery_key(key)
            else:
                runtime_error = (
                    'O pareamento anterior não foi concluído. '
                    'Tente sincronizar novamente.'
                )
    elif created:
        key = generate_master_key()
        key_store.save(key)
        recovery_once = format_recovery_key(key)
        pairing_required = False
    else:
        key = None
        pairing_required = True
    verifier_path = shared_root / 'key-verifier.json'
    try:
        verifier_missing = not verifier_path.exists()
        if key is not None and verifier_missing and (
            manifest.get('key_owner_device_uuid') == _device_uuid(local_root)
        ):
            verifier_header = {
                'format': 1,
                'kind': 'key-verifier',
                'deployment_id': str(manifest['deployment_id']),
            }
            _atomic_json(verifier_path, {
                'header': verifier_header,
                'encrypted': encrypt_json(key, {
                    'deployment_id': str(manifest['deployment_id']),
                    'verified': True,
                }, verifier_header),
            })
    except OSError:
        # Uma estação já pareada continua funcional offline. A outbox será
        # publicada quando o compartilhamento voltar.
        pass
    return SyncRuntime(
        True,
        local_root,
        shared_root,
        str(manifest['deployment_id']),
        device_uuid,
        key,
        pairing_required=pairing_required,
        recovery_key_once=recovery_once,
        error=runtime_error,
        initial_device=initial_device,
    )
