# This file contains utility functions that can be used throughout the application.

def hash_password(password: str) -> str:
    """Hash a password for storing."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against one provided by user."""
    return stored_password == hash_password(provided_password)

def generate_token(length: int = 16) -> str:
    """Generate a random token for session management."""
    import os
    return os.urandom(length).hex()