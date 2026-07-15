"""General helper functions."""
from hashlib import sha256
from re import sub


def stable_hash(value: str) -> str:
    """Return a deterministic SHA-256 hash for a string."""
    return sha256(value.encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    """Create a conservative URL-safe slug."""
    return sub(r"-+", "-", sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())).strip("-")
