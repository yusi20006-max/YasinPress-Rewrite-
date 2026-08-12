from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from .report import OperationalReport


class OperationalReportStore:
    """Persist hourly operational snapshots in the application's SQLite DB."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.ensure_schema()

    def ensure_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS operational_reports (
                timestamp TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def save(self, report: OperationalReport) -> None:
        payload = json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True)
        timestamp = report.timestamp.astimezone(UTC).isoformat()
        self.connection.execute(
            "INSERT OR REPLACE INTO operational_reports(timestamp, payload) VALUES (?, ?)",
            (timestamp, payload),
        )
        self.connection.commit()

    def latest(self) -> OperationalReport | None:
        row = self.connection.execute(
            "SELECT payload FROM operational_reports ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        data = json.loads(row[0])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return OperationalReport(**data)

    def hourly(self, limit: int = 24) -> list[OperationalReport]:
        rows = self.connection.execute(
            "SELECT payload FROM operational_reports ORDER BY timestamp DESC LIMIT ?",
            (max(1, limit),),
        ).fetchall()
        reports: list[OperationalReport] = []
        for (payload,) in rows:
            data = json.loads(payload)
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            reports.append(OperationalReport(**data))
        return reports
