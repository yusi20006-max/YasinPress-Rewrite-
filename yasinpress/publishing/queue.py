"""Persistent publication queue, fair scheduling, and rate control."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from yasinpress.database.models import Article, PublicationJob
from yasinpress.publishing import PublishResult, Publisher


@dataclass(frozen=True)
class QueueConfig:
    global_limit: int = 10
    source_limit: int = 5
    window: timedelta = timedelta(hours=1)
    lease: timedelta = timedelta(minutes=10)
    max_attempts: int = 3
    retry_base: timedelta = timedelta(seconds=30)


class ArticleStore(Protocol):
    def get(self, article_id: str) -> Article | None: ...


class SQLitePublicationQueueEngine:
    """Durable queue engine using one SQLite connection."""

    def __init__(self, connection: sqlite3.Connection, config: QueueConfig | None = None) -> None:
        self.db = connection
        self.db.row_factory = sqlite3.Row
        self.config = config or QueueConfig()
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS publication_queue (
                id TEXT PRIMARY KEY, article_id TEXT NOT NULL, destination TEXT NOT NULL,
                status TEXT NOT NULL, priority INTEGER NOT NULL, priority_level TEXT NOT NULL,
                source TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3, last_error TEXT,
                lease_expires_at TEXT, next_attempt_at TEXT, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS publication_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL,
                source TEXT NOT NULL, destination TEXT NOT NULL, published_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS publication_scheduler (
                id INTEGER PRIMARY KEY CHECK (id = 1), last_source TEXT
            );
            INSERT OR IGNORE INTO publication_scheduler(id, last_source) VALUES (1, NULL);
            CREATE INDEX IF NOT EXISTS idx_publication_queue_ready
              ON publication_queue(status, next_attempt_at, priority, created_at);
            CREATE INDEX IF NOT EXISTS idx_publication_events_time
              ON publication_events(published_at, source);
            """
        )
        self.db.commit()

    def enqueue(self, job: PublicationJob) -> None:
        self.db.execute(
            """INSERT OR IGNORE INTO publication_queue
               (id, article_id, destination, status, priority, priority_level, source,
                attempts, max_attempts, last_error, lease_expires_at, next_attempt_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job.id, job.article_id, job.destination, job.status, job.priority,
             job.priority_level, job.source, job.attempts, job.max_attempts, job.last_error,
             job.lease_expires_at.isoformat() if job.lease_expires_at else None,
             job.next_attempt_at.isoformat() if job.next_attempt_at else None,
             job.created_at.astimezone(UTC).isoformat()),
        )
        self.db.commit()

    def add_job(self, job: PublicationJob) -> None:
        self.enqueue(job)

    def exists(self, job_id: str) -> bool:
        return self.db.execute("SELECT 1 FROM publication_queue WHERE id=?", (job_id,)).fetchone() is not None

    def enqueue_article(self, article: Article, destination: str, *, priority: int,
                        priority_level: str, max_attempts: int | None = None) -> PublicationJob:
        job = PublicationJob(id=f"{article.id}:{destination}", article_id=article.id,
                             destination=destination, status="pending", priority=priority,
                             priority_level=priority_level, source=article.source,
                             max_attempts=max_attempts or self.config.max_attempts)
        self.enqueue(job)
        return job

    def recover_expired_leases(self, now: datetime | None = None) -> int:
        current = _utc(now)
        cur = self.db.execute(
            """UPDATE publication_queue SET
               status=CASE WHEN attempts >= max_attempts THEN 'dead_letter' ELSE 'retrying' END,
               next_attempt_at=CASE WHEN attempts >= max_attempts THEN NULL ELSE ? END,
               lease_expires_at=NULL
               WHERE status='processing' AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?""",
            (current.isoformat(), current.isoformat()))
        self.db.commit()
        return cur.rowcount

    def _recent_successes(self, now: datetime) -> list[sqlite3.Row]:
        cutoff = (now - self.config.window).isoformat()
        return self.db.execute(
            "SELECT source, destination FROM publication_events WHERE published_at > ? ORDER BY published_at",
            (cutoff,)).fetchall()

    def _reserved(self, now: datetime) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT source FROM publication_queue WHERE status='processing' AND lease_expires_at > ?",
            (now.isoformat(),)).fetchall()

    def _fair_source_order(self, sources: Iterable[str]) -> list[str]:
        unique = sorted(set(sources))
        if not unique:
            return []
        row = self.db.execute("SELECT last_source FROM publication_scheduler WHERE id=1").fetchone()
        last = row[0] if row else None
        if last in unique:
            idx = unique.index(last)
            return unique[idx + 1:] + unique[:idx + 1]
        return unique

    def claim_next(self, now: datetime | None = None) -> PublicationJob | None:
        """Atomically reserve the next fair job without exceeding rate limits."""
        current = _utc(now)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute(
                """UPDATE publication_queue SET
                   status=CASE WHEN attempts >= max_attempts THEN 'dead_letter' ELSE 'retrying' END,
                   next_attempt_at=CASE WHEN attempts >= max_attempts THEN NULL ELSE ? END,
                   lease_expires_at=NULL
                   WHERE status='processing' AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?""",
                (current.isoformat(), current.isoformat()))
            successes = self._recent_successes(current)
            reserved = self._reserved(current)
            if len(successes) + len(reserved) >= self.config.global_limit:
                self.db.rollback()
                return None
            source_successes: dict[str, int] = {}
            source_reserved: dict[str, int] = {}
            for row in successes:
                source_successes[row["source"]] = source_successes.get(row["source"], 0) + 1
            for row in reserved:
                source_reserved[row["source"]] = source_reserved.get(row["source"], 0) + 1
            rows = self.db.execute(
                """SELECT * FROM publication_queue
                   WHERE status IN ('pending','retrying')
                     AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
                   ORDER BY priority DESC, created_at ASC, id ASC""",
                (current.isoformat(),)).fetchall()
            if not rows:
                self.db.rollback()
                return None
            top_priority = rows[0]["priority"]
            candidates = [r for r in rows if r["priority"] == top_priority]
            order = self._fair_source_order(r["source"] for r in candidates)
            by_source: dict[str, list[sqlite3.Row]] = {source: [] for source in order}
            for row in candidates:
                by_source.setdefault(row["source"], []).append(row)
            selected = None
            for source in order:
                if source_successes.get(source, 0) + source_reserved.get(source, 0) >= self.config.source_limit:
                    continue
                if by_source.get(source):
                    selected = by_source[source][0]
                    break
            if selected is None:
                self.db.rollback()
                return None
            lease_until = current + self.config.lease
            changed = self.db.execute(
                "UPDATE publication_queue SET status='processing', attempts=attempts+1, lease_expires_at=? WHERE id=? AND status IN ('pending','retrying')",
                (lease_until.isoformat(), selected["id"])).rowcount
            if changed != 1:
                self.db.rollback()
                return None
            self.db.execute("UPDATE publication_scheduler SET last_source=? WHERE id=1", (selected["source"],))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return self.get(selected["id"])

    def get(self, job_id: str) -> PublicationJob | None:
        row = self.db.execute("SELECT * FROM publication_queue WHERE id=?", (job_id,)).fetchone()
        return _row_to_job(row) if row else None

    def mark_success(self, job_id: str, *, now: datetime | None = None) -> None:
        current = _utc(now)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT source,destination,status FROM publication_queue WHERE id=?", (job_id,)).fetchone()
            if not row or row["status"] != "processing":
                self.db.rollback()
                raise ValueError("job is not processing")
            self.db.execute("UPDATE publication_queue SET status='succeeded', lease_expires_at=NULL WHERE id=?", (job_id,))
            self.db.execute("INSERT INTO publication_events(job_id,source,destination,published_at) VALUES (?,?,?,?)",
                             (job_id, row["source"], row["destination"], current.isoformat()))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def mark_failure(self, job_id: str, error: str, *, now: datetime | None = None) -> PublicationJob:
        current = _utc(now)
        row = self.db.execute("SELECT * FROM publication_queue WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise KeyError(job_id)
        attempts = int(row["attempts"])
        if attempts >= int(row["max_attempts"]):
            status, next_at = "dead_letter", None
        else:
            delay = self.config.retry_base * (2 ** max(0, attempts - 1))
            status, next_at = "retrying", current + delay
        self.db.execute("UPDATE publication_queue SET status=?, last_error=?, lease_expires_at=NULL, next_attempt_at=? WHERE id=?",
                         (status, error, next_at.isoformat() if next_at else None, job_id))
        self.db.commit()
        return self.get(job_id)  # type: ignore[return-value]

    def metrics(self, now: datetime | None = None) -> dict[str, int]:
        current = _utc(now)
        successes = self._recent_successes(current)
        reserved = self._reserved(current)
        rows = self.db.execute("SELECT status,COUNT(*) AS count FROM publication_queue GROUP BY status").fetchall()
        counts = {r["status"]: int(r["count"]) for r in rows}
        return {
            "queue_depth": counts.get("pending", 0) + counts.get("retrying", 0),
            "pending": counts.get("pending", 0), "processing": counts.get("processing", 0),
            "retrying": counts.get("retrying", 0), "failed": counts.get("failed", 0),
            "dead_letter": counts.get("dead_letter", 0), "succeeded": counts.get("succeeded", 0),
            "published_last_hour": len(successes), "reserved_last_hour": len(reserved),
            "remaining_global_capacity": max(0, self.config.global_limit - len(successes) - len(reserved)),
        }

    def run_once(self, publishers: dict[str, Publisher], articles: ArticleStore,
                 *, now: datetime | None = None) -> PublishResult | None:
        job = self.claim_next(now)
        if job is None:
            return None
        article = articles.get(job.article_id)
        if article is None:
            return self._fail_result(job, "article not found", now)
        publisher = publishers.get(job.destination)
        if publisher is None:
            return self._fail_result(job, "publisher unavailable", now)
        try:
            result = publisher.publish(article)
        except Exception as exc:
            result = PublishResult(False, job.destination, error=str(exc))
        if result.success:
            self.mark_success(job.id, now=now)
        else:
            self.mark_failure(job.id, result.error or "publication failed", now=now)
        return result

    def _fail_result(self, job: PublicationJob, error: str, now: datetime | None) -> PublishResult:
        self.mark_failure(job.id, error, now=now)
        return PublishResult(False, job.destination, error=error)


def _utc(value: datetime | None) -> datetime:
    current = value or datetime.now(UTC)
    return current.replace(tzinfo=UTC) if current.tzinfo is None else current.astimezone(UTC)


def _row_to_job(row: sqlite3.Row) -> PublicationJob:
    def dt(name: str) -> datetime | None:
        value = row[name]
        if not value:
            return None
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return PublicationJob(
        id=row["id"], article_id=row["article_id"], destination=row["destination"],
        status=row["status"], priority=row["priority"], priority_level=row["priority_level"],
        source=row["source"], attempts=row["attempts"], max_attempts=row["max_attempts"],
        last_error=row["last_error"], lease_expires_at=dt("lease_expires_at"),
        next_attempt_at=dt("next_attempt_at"), created_at=dt("created_at") or datetime.now(UTC),
    )
