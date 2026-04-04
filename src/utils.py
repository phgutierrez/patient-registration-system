from werkzeug.security import generate_password_hash, check_password_hash
import secrets


def hash_password(password: str) -> str:
    """Mantido por compatibilidade; usa Werkzeug em vez de SHA-256 simples."""
    return generate_password_hash(password)


def verify_password(stored_password: str, provided_password: str) -> bool:
    """Valida hashes gerados pelo Werkzeug."""
    return check_password_hash(stored_password, provided_password)


def generate_token(length: int = 32) -> str:
    """Gera token criptograficamente seguro para fluxos temporários."""
    return secrets.token_hex(length)
