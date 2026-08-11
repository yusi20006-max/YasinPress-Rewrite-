"""CLI status command."""

from yasinpress.monitoring.health import check_health


def status_text() -> str:
    """Return human-readable status."""
    return "healthy" if check_health().healthy else "unhealthy"
