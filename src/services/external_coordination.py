"""Coordenação leve de efeitos externos entre estações.

Os nomes e conteúdos usados no compartilhamento contêm somente UUIDs e
metadados operacionais; nenhum dado clínico é gravado fora dos envelopes
criptografados.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from src.sync import sync_service


@dataclass
class ExternalLock:
    acquired: bool
    available: bool
    attempt_uuid: str
    path: Path | None = None
    message: str | None = None

    def release(self) -> None:
        if not self.acquired or self.path is None:
            return
        try:
            (self.path / 'owner.json').unlink(missing_ok=True)
            self.path.rmdir()
        except OSError:
            pass
        self.acquired = False


def acquire_forms_lock(entity_uuid: str, stale_after: int = 180) -> ExternalLock:
    runtime = sync_service.runtime
    attempt_uuid = str(uuid.uuid4())
    if not runtime or not runtime.ready or not runtime.shared_root:
        return ExternalLock(
            False, False, attempt_uuid,
            message='A pasta de sincronização não está disponível.',
        )
    lock_root = runtime.shared_root / 'locks' / 'google-forms'
    lock_path = lock_root / entity_uuid
    try:
        lock_root.mkdir(parents=True, exist_ok=True)
        try:
            lock_path.mkdir()
        except FileExistsError:
            owner_path = lock_path / 'owner.json'
            try:
                owner = json.loads(owner_path.read_text(encoding='utf-8'))
                created_at = float(owner.get('created_at_epoch', 0))
            except (OSError, ValueError, TypeError):
                created_at = 0
            if created_at and time.time() - created_at <= stale_after:
                return ExternalLock(
                    False, True, attempt_uuid,
                    message='Outra estação já está enviando esta solicitação.',
                )
            # Trava abandonada. A remoção é segura porque o nome é um UUID
            # validado internamente, nunca um caminho informado pelo cliente.
            owner_path.unlink(missing_ok=True)
            try:
                lock_path.rmdir()
                lock_path.mkdir()
            except OSError:
                return ExternalLock(
                    False, True, attempt_uuid,
                    message='A tentativa anterior ainda está sendo finalizada.',
                )

        owner = {
            'attempt_uuid': attempt_uuid,
            'device_uuid': runtime.device_uuid,
            'created_at_epoch': time.time(),
        }
        temporary = lock_path / f'.{attempt_uuid}.tmp'
        with temporary.open('w', encoding='utf-8') as handle:
            json.dump(owner, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, lock_path / 'owner.json')
        return ExternalLock(True, True, attempt_uuid, lock_path)
    except OSError:
        return ExternalLock(
            False, False, attempt_uuid,
            message='Não foi possível acessar a pasta de sincronização.',
        )
