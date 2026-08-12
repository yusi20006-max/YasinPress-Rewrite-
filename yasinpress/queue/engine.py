from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Callable

from yasinpress.database.models import PublicationJob


@dataclass(frozen=True)
class QueueLimits:
    global_per_hour: int = 10
    source_per_hour: int = 5
    lease_seconds: int = 300
    max_attempts: int = 3
    backoff_base_seconds: int = 30


class PublicationQueue:
    """Durable, fair publication scheduler backed by SQLite."""

    def __init__(self, connection: sqlite3.Connection, limits: QueueLimits | None = None) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row
        self.limits = limits or QueueLimits()
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS publication_queue (
                id TEXT PRIMARY KEY, article_id TEXT NOT NULL, destination TEXT NOT NULL,
                status TEXT NOT NULL, priority INTEGER NOT NULL, priority_level TEXT NOT NULL,
                source TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3, last_error TEXT,
                lease_expires_at TEXT, next_attempt_at TEXT, created_at TEXT NOT NULL
            )"""
        )
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS publication_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL,
                source TEXT NOT NULL, destination TEXT NOT NULL, success INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        self.connection.commit()

    def enqueue(self, job: PublicationJob) -> None:
        self.connection.execute(
            """INSERT OR IGNORE INTO publication_queue
            (id,article_id,destination,status,priority,priority_level,source,attempts,
             max_attempts,last_error,lease_expires_at,next_attempt_at,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (job.id, job.article_id, job.destination, "pending", job.priority,
             job.priority_level, job.source, job.attempts, job.max_attempts,
             job.last_error, None, job.next_attempt_at.isoformat() if job.next_attempt_at else None,
             job.created_at.isoformat()),
        )
        self.connection.commit()

    def recover_stale_leases(self, now: datetime | None = None) -> int:
        now = self._utc(now)
        cur = self.connection.execute(
            """UPDATE publication_queue SET status='retrying', lease_expires_at=NULL,
               next_attempt_at=? WHERE status='processing' AND lease_expires_at IS NOT NULL
               AND lease_expires_at <= ?""",
            (now.isoformat(), now.isoformat()),
        )
        self.connection.commit()
        return cur.rowcount

    def claim(self, now: datetime | None = None) -> PublicationJob | None:
        now = self._utc(now)
        self.recover_stale_leases(now)
        cutoff = now - timedelta(hours=1)
        global_count = self._successful_count(cutoff, None)
        if global_count >= self.limits.global_per_hour:
            return None

        rows = self.connection.execute(
            """SELECT * FROM publication_queue
               WHERE status IN ('pending','retrying')
                 AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
               ORDER BY priority DESC, created_at ASC""",
            (now.isoformat(),),
        ).fetchall()
        if not rows:
            return None

        jobs = [self._row(row) for row in rows]
        # Fairness is applied inside each priority tier: among eligible sources,
        # prefer the source with the fewest successful publications in the window.
        min_count = None
        chosen = None
        for job in jobs:
            count = self._successful_count(cutoff, job.source)
            if count >= self.limits.source_per_hour:
                continue
            if min_count is None or count < min_count:
                min_count = count
                chosen = job
        if chosen is None:
            return None

        lease = now + timedelta(seconds=self.limits.lease_seconds)
        cur = self.connection.execute(
            """UPDATE publication_queue SET status='processing', lease_expires_at=?
               WHERE id=? AND status IN ('pending','retrying')""",
            (lease.isoformat(), chosen.id),
        )
        self.connection.commit()
        if cur.rowcount != 1:
            return None
        chosen.status = "processing"
        chosen.lease_expires_at = lease
        return chosen

    def succeed(self, job_id: str, now: datetime | None = None) -> None:
        self._finish(job_id, True, now)

    def fail(self, job_id: str, error: str, now: datetime | None = None) -> None:
        now = self._utc(now)
        row = self.connection.execute("SELECT * FROM publication_queue WHERE id=?", (job_id,)).fetchone()
        if row is None:
            return
        attempts = int(row["attempts"]) + 1
        max_attempts = int(row["max_attempts"] or self.limits.max_attempts)
        if attempts >= max_attempts:
            status = "dead_letter"
            next_attempt = None
        else:
            status = "retrying"
            delay = self.limits.backoff_base_seconds * (2 ** (attempts - 1))
            next_attempt = now + timedelta(seconds=delay)
        self.connection.execute(
            """UPDATE publication_queue SET status=?, attempts=?, last_error=?,
               lease_expires_at=NULL, next_attempt_at=? WHERE id=?""",
            (status, attempts, error, next_attempt.isoformat() if next_attempt else None, job_id),
        )
        self.connection.commit()

    def metrics(self) -> dict[str, int]:
        rows = self.connection.execute("SELECT status, COUNT(*) c FROM publication_queue GROUP BY status").fetchall()
        result = {row["status"]: int(row["c"]) for row in rows}
        result["queue_depth"] = sum(result.get(s, 0) for s in ("pending", "processing", "retrying"))
        return result

    def _finish(self, job_id: str, success: bool, now: datetime | None) -> None:
        now = self._utc(now)
        row = self.connection.execute("SELECT source,destination FROM publication_queue WHERE id=?", (job_id,)).fetchone()
        if row is None:
            return
        status = "succeeded" if success else "failed"
        self.connection.execute(
            "UPDATE publication_queue SET status=?, lease_expires_at=NULL WHERE id=? AND status='processing'",
            (status, job_id),
        )
        self.connection.execute(
            "INSERT INTO publication_events(job_id,source,destination,success,created_at) VALUES(?,?,?,?,?)",
            (job_id, row["source"], row["destination"], int(success), now.isoformat()),
        )
        self.connection.commit()

    def _successful_count(self, cutoff: datetime, source: str | None) -> int:
        if source is None:
            row = self.connection.execute(
                "SELECT COUNT(*) c FROM publication_events WHERE success=1 AND created_at >= ?",
                (cutoff.isoformat(),),
            ).fetchone()
        else:
            row = self.connection.execute(
                "SELECT COUNT(*) c FROM publication_events WHERE success=1 AND source=? AND created_at >= ?",
                (source, cutoff.isoformat()),
            ).fetchone()
        return int(row["c"])

    @staticmethod
    def _utc(value: datetime | None) -> datetime:
        value = value or datetime.now(UTC)
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @staticmethod
    def _row(row: sqlite3.Row) -> PublicationJob:
        def dt(value: str | None) -> datetime | None:
            return datetime.fromisoformat(value) if value else None
        return PublicationJob(
            id=row["id"], article_id=row["article_id"], destination=row["destination"],
            status=row["status"], priority=row["priority"], priority_level=row["priority_level"],
            source=row["source"], attempts=row["attempts"], max_attempts=row["max_attempts"],
            last_error=row["last_error"], lease_expires_at=dt(row["lease_expires_at"]),
            next_attempt_at=dt(row["next_attempt_at"]), created_at=dt(row["created_at"]) or datetime.now(UTC),
        )
