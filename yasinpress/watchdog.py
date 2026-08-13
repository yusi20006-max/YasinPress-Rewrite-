from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class WatchdogStatus:
    last_tick_at: datetime | None
    consecutive_failures: int
    healthy: bool
    last_error: str | None
    stale: bool


class Watchdog:
    """Runtime supervisor with explicit stale detection and recovery state."""

    def __init__(self, stale_after: timedelta | float = timedelta(minutes=2)) -> None:
        if isinstance(stale_after, (int, float)):
            stale_after = timedelta(seconds=stale_after)
        if stale_after <= timedelta(0):
            raise ValueError("stale_after must be positive")
        self.stale_after = stale_after
        self.last_tick_at: datetime | None = None
        self.consecutive_failures = 0
        self.last_error: str | None = None

    def record_success(self, now: datetime | None = None) -> None:
        self.last_tick_at = _utc(now)
        self.consecutive_failures = 0
        self.last_error = None

    def record_failure(self, error: Exception | str, now: datetime | None = None) -> None:
        self.last_tick_at = _utc(now)
        self.consecutive_failures += 1
        self.last_error = str(error)

    def status(self, now: datetime | None = None) -> WatchdogStatus:
        current = _utc(now)
        stale = self.last_tick_at is None or current - self.last_tick_at > self.stale_after
        return WatchdogStatus(
            self.last_tick_at,
            self.consecutive_failures,
            not stale and self.consecutive_failures == 0,
            self.last_error,
            stale,
        )

    def is_stale(self, now: datetime | None = None) -> bool:
        return self.status(now).stale


def _utc(value: datetime | None) -> datetime:
    current = value or datetime.now(UTC)
    return current.replace(tzinfo=UTC) if current.tzinfo is None else current.astimezone(UTC)
