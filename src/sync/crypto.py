"""Criptografia autenticada e proteção local da chave de implantação."""
from __future__ import annotations

import base64
import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path


class SyncCryptoError(RuntimeError):
    pass


def generate_master_key() -> bytes:
    return os.urandom(32)


def format_recovery_key(key: bytes) -> str:
    encoded = base64.b32encode(key).decode('ascii').rstrip('=')
    return '-'.join(encoded[index:index + 4] for index in range(0, len(encoded), 4))


def parse_recovery_key(value: str) -> bytes:
    normalized = ''.join(ch for ch in (value or '').upper() if ch.isalnum())
    padding = '=' * ((8 - len(normalized) % 8) % 8)
    try:
        key = base64.b32decode(normalized + padding, casefold=True)
    except Exception as exc:
        raise SyncCryptoError('Chave de recuperação inválida.') from exc
    if len(key) != 32:
        raise SyncCryptoError('A chave de recuperação deve representar 256 bits.')
    return key


def _aes():
    try:
        from Crypto.Cipher import AES
    except ImportError as exc:
        raise SyncCryptoError(
            'PyCryptodome não está instalado; execute novamente o setup.'
        ) from exc
    return AES


def encrypt_json(key: bytes, value: dict, associated_data: dict) -> dict:
    nonce = os.urandom(12)
    aad = json.dumps(
        associated_data, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    plaintext = json.dumps(
        value, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    cipher = _aes().new(key, _aes().MODE_GCM, nonce=nonce, mac_len=16)
    cipher.update(aad)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return {
        'nonce': base64.b64encode(nonce).decode('ascii'),
        'tag': base64.b64encode(tag).decode('ascii'),
        'ciphertext': base64.b64encode(ciphertext).decode('ascii'),
    }


def decrypt_json(key: bytes, encrypted: dict, associated_data: dict) -> dict:
    aad = json.dumps(
        associated_data, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    try:
        nonce = base64.b64decode(encrypted['nonce'], validate=True)
        tag = base64.b64decode(encrypted['tag'], validate=True)
        ciphertext = base64.b64decode(encrypted['ciphertext'], validate=True)
        cipher = _aes().new(key, _aes().MODE_GCM, nonce=nonce, mac_len=16)
        cipher.update(aad)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        result = json.loads(plaintext.decode('utf-8'))
    except Exception as exc:
        raise SyncCryptoError(
            'Evento criptografado inválido, adulterado ou criado com outra chave.'
        ) from exc
    if not isinstance(result, dict):
        raise SyncCryptoError('Conteúdo criptografado não é um objeto válido.')
    return result


class _DataBlob(ctypes.Structure):
    _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]


def _blob(data: bytes):
    buffer = ctypes.create_string_buffer(data)
    return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer


def _dpapi_protect(data: bytes) -> bytes:
    if os.name != 'nt':
        return data
    source, source_buffer = _blob(data)
    output = _DataBlob()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    flags = 0x1  # CRYPTPROTECT_UI_FORBIDDEN
    if not crypt32.CryptProtectData(
        ctypes.byref(source), 'PatientRegistration Sync', None, None, None,
        flags, ctypes.byref(output),
    ):
        raise SyncCryptoError('O Windows não conseguiu proteger a chave local.')
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        kernel32.LocalFree(output.pbData)
        del source_buffer


def _dpapi_unprotect(data: bytes) -> bytes:
    if os.name != 'nt':
        return data
    source, source_buffer = _blob(data)
    output = _DataBlob()
    description = wintypes.LPWSTR()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    flags = 0x1
    if not crypt32.CryptUnprotectData(
        ctypes.byref(source), ctypes.byref(description), None, None, None,
        flags, ctypes.byref(output),
    ):
        raise SyncCryptoError(
            'A chave local pertence a outro usuário do Windows ou está corrompida.'
        )
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        kernel32.LocalFree(output.pbData)
        if description:
            kernel32.LocalFree(description)
        del source_buffer


class LocalKeyStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.is_file()

    def save(self, key: bytes) -> None:
        if len(key) != 32:
            raise SyncCryptoError('Chave mestra inválida.')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f'.{self.path.name}.{os.getpid()}.tmp')
        protected = _dpapi_protect(key)
        with temporary.open('wb') as handle:
            handle.write(protected)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.path)
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def load(self) -> bytes:
        try:
            key = _dpapi_unprotect(self.path.read_bytes())
        except OSError as exc:
            raise SyncCryptoError('Não foi possível ler a chave local.') from exc
        if len(key) != 32:
            raise SyncCryptoError('A chave local possui tamanho inválido.')
        return key
