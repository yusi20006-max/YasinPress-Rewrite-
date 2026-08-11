"""Secret helpers."""

import secrets


def generate_secret(length: int = 32) -> str:
    """Generate a URL-safe secret."""
    return secrets.token_urlsafe(length)
