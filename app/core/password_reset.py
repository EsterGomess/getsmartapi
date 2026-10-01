"""Utilities for secure password recovery tokens."""
import hashlib
import secrets


def generate_password_reset_token() -> str:
    """Generate a cryptographically secure token for a recovery link."""
    return secrets.token_urlsafe(32)


def hash_password_reset_token(token: str) -> str:
    """Return the SHA-256 digest stored in the database for a raw token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
