from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .report import OperationalReport


@dataclass
class HourlyReportScheduler:
    """Generate exactly one operational snapshot for each UTC hour."""

    reporter: callable
    last_hour: datetime | None = None

    def due(self, now: datetime | None = None) -> bool:
        current = (now or datetime.now(UTC)).astimezone(UTC).replace(
            minute=0, second=0, microsecond=0
        )
        return self.last_hour != current

    def run_if_due(self, now: datetime | None = None) -> OperationalReport | None:
        current = (now or datetime.now(UTC)).astimezone(UTC).replace(
            minute=0, second=0, microsecond=0
        )
        if self.last_hour == current:
            return None
        report = self.reporter()
        self.last_hour = current
        return report
