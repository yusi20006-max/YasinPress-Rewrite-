"""Health checks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthStatus:
    """Health check result."""

    healthy: bool
    details: dict[str, str]


def check_health() -> HealthStatus:
    """Return application health."""
    return HealthStatus(True, {"status": "ok"})
