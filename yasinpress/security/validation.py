"""Security validation."""

from urllib.parse import urlparse


def validate_public_url(url: str) -> None:
    """Validate an HTTP(S) URL."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Expected an absolute HTTP(S) URL")
