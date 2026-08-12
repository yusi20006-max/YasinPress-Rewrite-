from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from yasinpress.monitoring.dispatcher import HourlyReportDispatcher
from yasinpress.publishing.queue import SQLitePublicationQueueEngine


class PublicationWorker:
    """Single runtime worker that drains the persistent queue and emits reports."""

    def __init__(
        self,
        queue: SQLitePublicationQueueEngine,
        publish_once: Callable[[], object | None],
        reports: HourlyReportDispatcher | None = None,
    ) -> None:
        self.queue = queue
        self.publish_once = publish_once
        self.reports = reports
        self.last_tick_at: datetime | None = None

    def tick(self, now: datetime | None = None) -> object | None:
        current = _utc(now)
        self.queue.recover_expired_leases(current)
        result = self.publish_once()
        self.last_tick_at = current
        if self.reports is not None:
            self.reports.dispatch(self.queue, now=current)
        return result

    def run_for(self, duration: timedelta, interval: timedelta = timedelta(seconds=1)) -> None:
        if duration <= timedelta(0) or interval <= timedelta(0):
            raise ValueError("duration and interval must be positive")
        deadline = datetime.now(UTC) + duration
        while datetime.now(UTC) < deadline:
            self.tick()
            # This worker intentionally leaves sleeping/scheduling to Runtime.
            break


def _utc(value: datetime | None) -> datetime:
    current = value or datetime.now(UTC)
    return current.replace(tzinfo=UTC) if current.tzinfo is None else current.astimezone(UTC)
