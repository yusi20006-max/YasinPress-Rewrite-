"""API routes."""

from yasinpress.monitoring.health import check_health

from .responses import Response, ok


def health_route() -> Response:
    """Return health endpoint response."""
    status = check_health()
    return ok({"healthy": status.healthy, "details": status.details})
