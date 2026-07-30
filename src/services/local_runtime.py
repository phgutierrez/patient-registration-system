"""Relançamento local de uma distribuição PyInstaller aberta por SMB."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path


APP_RUNTIME_VERSION = '2.1.0-sync1'
DRIVE_REMOTE = 4


def is_remote_path(path: Path) -> bool:
    text = str(path)
    if text.startswith('\\\\') or text.startswith('//'):
        return True
    if os.name != 'nt':
        return False
    anchor = path.resolve().anchor
    if not anchor:
        return False
    try:
        return ctypes.windll.kernel32.GetDriveTypeW(anchor) == DRIVE_REMOTE
    except Exception:
        return False


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
    with temporary.open('w', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _deployment_manifest(shared_data: Path) -> dict:
    path = shared_data / 'deployment.json'
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        if value.get('deployment_id'):
            return value
    except (OSError, ValueError, AttributeError):
        pass

    shared_data.mkdir(parents=True, exist_ok=True)
    lock = shared_data / '.launcher-initialize-lock'
    try:
        lock.mkdir()
        owns_lock = True
    except FileExistsError:
        owns_lock = False
    if owns_lock:
        try:
            try:
                value = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                value = {
                    'deployment_id': str(uuid.uuid4()),
                    'sync_schema_version': 1,
                    'launcher_version': APP_RUNTIME_VERSION,
                }
                _atomic_json(path, value)
            return value
        finally:
            try:
                lock.rmdir()
            except OSError:
                pass

    import time
    for _ in range(100):
        time.sleep(0.1)
        try:
            value = json.loads(path.read_text(encoding='utf-8'))
            if value.get('deployment_id'):
                return value
        except (OSError, ValueError):
            continue
    raise RuntimeError('Outra estação não concluiu a inicialização da implantação.')


def _build_identity(source_root: Path) -> str:
    manifest = source_root / 'build_manifest.json'
    if manifest.is_file():
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()[:16]
        return f'{APP_RUNTIME_VERSION}-{digest}'
    executable = Path(sys.executable)
    signature = (
        f'{APP_RUNTIME_VERSION}:{executable.name}:'
        f'{executable.stat().st_size}:{executable.stat().st_mtime_ns}'
    )
    return f'{APP_RUNTIME_VERSION}-{hashlib.sha256(signature.encode()).hexdigest()[:16]}'


def _copy_distribution(source_root: Path, destination: Path) -> None:
    if destination.is_dir() and (destination / Path(sys.executable).name).is_file():
        return
    temporary = destination.with_name(
        f'.{destination.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp'
    )
    if temporary.exists():
        shutil.rmtree(temporary)

    excluded = {
        '_shared_data', 'instance', 'logs', 'protected_pdfs',
        'backup', 'build', 'dist', '.venv', '.venv32', '.git',
    }

    def ignore(_directory, names):
        return {
            name for name in names
            if name in excluded
            or name.lower() == '.env'
            or name.lower().endswith('.db')
        }

    shutil.copytree(source_root, temporary, ignore=ignore)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.replace(temporary, destination)
    except OSError:
        if destination.exists():
            shutil.rmtree(temporary, ignore_errors=True)
        else:
            raise


def _local_device_uuid(local_data: Path) -> str:
    path = local_data / 'device.json'
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        if value.get('device_uuid'):
            return str(value['device_uuid'])
    except (OSError, ValueError, AttributeError):
        pass
    device_uuid = str(uuid.uuid4())
    _atomic_json(path, {'device_uuid': device_uuid})
    return device_uuid


def _claim_legacy_seed(shared_data: Path, device_uuid: str) -> bool:
    """Reserva a migração do banco compartilhado antigo para uma estação."""
    manifest_path = shared_data / 'deployment.json'
    lock = shared_data / '.legacy-migration-lock'
    try:
        lock.mkdir()
        owns_lock = True
    except FileExistsError:
        owns_lock = False
    if not owns_lock:
        import time
        for _ in range(100):
            time.sleep(0.1)
            try:
                manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
                owner = manifest.get('legacy_seed_device')
                if owner:
                    return owner == device_uuid
            except (OSError, ValueError):
                continue
        raise RuntimeError('Outra estação não concluiu a migração inicial.')
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        owner = manifest.get('legacy_seed_device')
        if not owner:
            manifest['legacy_seed_device'] = device_uuid
            manifest['legacy_seed_claimed_at'] = datetime.utcnow().isoformat() + 'Z'
            _atomic_json(manifest_path, manifest)
            return True
        return owner == device_uuid
    finally:
        try:
            lock.rmdir()
        except OSError:
            pass


def _migrate_legacy_database(source_root: Path, local_data: Path, shared_data: Path) -> None:
    """Cria uma cópia SQLite consistente e privada na primeira estação."""
    target = local_data / 'instance' / 'prontuario.db'
    if target.is_file():
        return
    source = source_root / 'instance' / 'prontuario.db'
    if not source.is_file():
        return

    device_uuid = _local_device_uuid(local_data)
    if not _claim_legacy_seed(shared_data, device_uuid):
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f'.{target.name}.{uuid.uuid4().hex}.tmp')
    source_uri = source.resolve().as_uri() + '?mode=ro'
    source_db = sqlite3.connect(source_uri, uri=True, timeout=10)
    try:
        result = source_db.execute('PRAGMA quick_check').fetchone()
        if not result or result[0] != 'ok':
            raise RuntimeError(
                'O banco SQLite antigo falhou no PRAGMA quick_check. '
                'Restaure o backup antes de iniciar a implantação.'
            )
        destination_db = sqlite3.connect(str(temporary))
        try:
            source_db.backup(destination_db)
            destination_db.commit()
            copied_check = destination_db.execute('PRAGMA quick_check').fetchone()
            if not copied_check or copied_check[0] != 'ok':
                raise RuntimeError('A cópia local do banco antigo ficou inválida.')
        finally:
            destination_db.close()
    finally:
        source_db.close()
    os.replace(temporary, target)

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_root = local_data / 'migration_backup' / stamp
    backup_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup_root / 'prontuario.db')
    env_file = source_root / '.env'
    if env_file.is_file():
        shutil.copy2(env_file, backup_root / '.env.backup')
    for pdf_source in (
        source_root / 'instance' / 'protected_pdfs',
        source_root / 'src' / 'static' / 'pdfs' / 'gerados',
    ):
        if pdf_source.is_dir():
            shutil.copytree(
                pdf_source,
                backup_root / ('pdfs_' + pdf_source.name),
                dirs_exist_ok=True,
            )

def maybe_relaunch_frozen_from_share(arguments: list[str] | None = None) -> bool:
    """Retorna True no processo da rede após iniciar a cópia local."""
    if not getattr(sys, 'frozen', False):
        return False
    if os.getenv('PRS_LOCAL_RELAUNCHED') == '1':
        return False

    source_root = Path(sys.executable).resolve().parent
    if not is_remote_path(source_root):
        return False

    shared_data = source_root / '_shared_data'
    manifest = _deployment_manifest(shared_data)
    deployment_id = str(manifest['deployment_id'])
    local_app_data = Path(
        os.getenv('LOCALAPPDATA')
        or (Path.home() / 'AppData' / 'Local')
    )
    product_root = local_app_data / 'PatientRegistrationSystem'
    version = _build_identity(source_root)
    local_distribution = product_root / 'applications' / deployment_id / version
    local_data = product_root / 'data' / deployment_id
    _copy_distribution(source_root, local_distribution)
    local_data.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_database(source_root, local_data, shared_data)

    local_executable = local_distribution / Path(sys.executable).name
    if not local_executable.is_file():
        raise RuntimeError('A cópia local do executável ficou incompleta.')
    environment = os.environ.copy()
    environment.update({
        'PRS_LOCAL_RELAUNCHED': '1',
        'PRS_DEPLOYMENT_ROOT': str(source_root),
        'PRS_LOCAL_DATA_ROOT': str(local_data),
        'APP_DATA_DIR': str(local_data),
        'SYNC_ENABLED': 'true',
        'SYNC_ROOT': str(shared_data),
        'SYNC_INTERVAL_SECONDS': '5',
    })
    subprocess.Popen(
        [str(local_executable), *(arguments or sys.argv[1:])],
        cwd=str(local_distribution),
        env=environment,
        close_fds=True,
    )
    return True
