import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from werkzeug.security import check_password_hash, generate_password_hash

from src.core.config import get_settings


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return check_password_hash(hashed, password)


def _build_token(payload: Dict[str, Any], expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    data = payload.copy()
    data.update({'iat': now, 'exp': now + expires_delta})
    return jwt.encode(data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int, role: str) -> str:
    settings = get_settings()
    return _build_token({'sub': str(user_id), 'role': role, 'type': 'access'}, timedelta(minutes=settings.jwt_access_ttl_min))


def create_refresh_token(user_id: int, role: str, jti: str) -> str:
    settings = get_settings()
    return _build_token({'sub': str(user_id), 'role': role, 'jti': jti, 'type': 'refresh'}, timedelta(days=settings.jwt_refresh_ttl_days))


def decode_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError('invalid_token') from exc


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)
