from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from yasinpress.monitoring import hourly_report, snapshot


@dataclass(frozen=True)
class ReportDelivery:
    sent_at: datetime
    payload: dict[str, object]
    success: bool
    error: str | None = None


class HourlyReportDispatcher:
    """Emit at most one report per configured hour and survive delivery errors."""

    def __init__(self, sender: Callable[[dict[str, object]], None], interval: timedelta = timedelta(hours=1)) -> None:
        if interval <= timedelta(0):
            raise ValueError("interval must be positive")
        self.sender = sender
        self.interval = interval
        self.last_sent_at: datetime | None = None
        self.last_delivery: ReportDelivery | None = None

    def due(self, now: datetime | None = None) -> bool:
        current = _utc(now)
        return self.last_sent_at is None or current - self.last_sent_at >= self.interval

    def dispatch(self, queue, *, now: datetime | None = None) -> ReportDelivery | None:
        current = _utc(now)
        if not self.due(current):
            return None
        payload = hourly_report(snapshot(queue))
        try:
            self.sender(payload)
        except Exception as exc:  # delivery boundary must not kill runtime
            delivery = ReportDelivery(current, payload, False, str(exc))
        else:
            self.last_sent_at = current
            delivery = ReportDelivery(current, payload, True)
        self.last_delivery = delivery
        return delivery


def _utc(value: datetime | None) -> datetime:
    current = value or datetime.now(UTC)
    return current.replace(tzinfo=UTC) if current.tzinfo is None else current.astimezone(UTC)
