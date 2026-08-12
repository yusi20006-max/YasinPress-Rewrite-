from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime

from yasinpress.database.models import Article, PublicationJob
from yasinpress.publishing.history import DeliveryRecord


class SQLiteArticleRepository:
    """Persistence adapter for normalized Article records."""

    def __init__(
        self, path: str = ":memory:", connection: sqlite3.Connection | None = None
    ) -> None:
        self._owns_connection = connection is None
        self.connection = connection or sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("""CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL,
            content TEXT NOT NULL, source TEXT NOT NULL,
            published_at TEXT NOT NULL, category TEXT,
            event_id TEXT, received_at TEXT, lifecycle_state TEXT,
            ai_state TEXT, ai_error TEXT, source_metadata TEXT)""")
        for column in [
            "event_id",
            "received_at",
            "lifecycle_state",
            "ai_state",
            "ai_error",
            "source_metadata",
        ]:
            try:
                self.connection.execute(f"ALTER TABLE articles ADD COLUMN {column} TEXT")
            except sqlite3.OperationalError:
                pass
        self.connection.commit()

    def save(self, article: Article) -> None:
        self.connection.execute(
            """INSERT INTO articles(
                id, title, url, content, source, published_at, category,
                event_id, received_at, lifecycle_state, ai_state, ai_error, source_metadata
               )
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
               title=excluded.title, url=excluded.url, content=excluded.content,
               source=excluded.source, published_at=excluded.published_at, category=excluded.category,
               event_id=excluded.event_id, received_at=excluded.received_at, lifecycle_state=excluded.lifecycle_state,
               ai_state=excluded.ai_state, ai_error=excluded.ai_error, source_metadata=excluded.source_metadata""",
            (
                article.id,
                article.title,
                article.url,
                article.content,
                article.source,
                article.published_at.isoformat()
                if hasattr(article.published_at, "isoformat")
                else article.published_at,
                article.category,
                article.event_id,
                article.received_at.isoformat()
                if hasattr(article.received_at, "isoformat")
                else article.received_at,
                article.lifecycle_state,
                article.ai_state,
                article.ai_error,
                article.source_metadata,
            ),
        )
        self.connection.commit()

    def save_many(self, articles: Iterable[Article]) -> None:
        for article in articles:
            self.save(article)

    def exists(self, article_id: str) -> bool:
        """Return whether an article exists."""
        row = self.connection.execute(
            "SELECT 1 FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
        return row is not None

    def get(self, article_id: str) -> Article | None:
        row = self.connection.execute(
            "SELECT * FROM articles WHERE id=? OR url=? LIMIT 1", (article_id, article_id)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_article(row)

    def all(self) -> tuple[Article, ...]:
        rows = self.connection.execute(
            "SELECT * FROM articles ORDER BY published_at DESC"
        ).fetchall()
        return tuple(self._row_to_article(row) for row in rows)

    def _row_to_article(self, row) -> Article:
        def get_col(name, default=None):
            try:
                return row[name]
            except (IndexError, KeyError):
                return default

        pub_str = get_col("published_at")
        pub = datetime.fromisoformat(pub_str) if pub_str else datetime.now(UTC)

        rec_str = get_col("received_at")
        rec = datetime.fromisoformat(rec_str) if rec_str else datetime.now(UTC)

        return Article(
            id=get_col("id"),
            title=get_col("title"),
            url=get_col("url"),
            content=get_col("content"),
            source=get_col("source"),
            published_at=pub,
            category=get_col("category"),
            event_id=get_col("event_id"),
            received_at=rec,
            lifecycle_state=get_col("lifecycle_state", "fetched"),
            ai_state=get_col("ai_state", "none"),
            ai_error=get_col("ai_error"),
            source_metadata=get_col("source_metadata"),
        )

    def close(self) -> None:
        if self._owns_connection:
            self.connection.close()


class SQLiteDeliveryHistory:
    """Durable delivery history backed by the shared application connection."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.execute("""CREATE TABLE IF NOT EXISTS delivery_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, article_id TEXT NOT NULL,
            destination TEXT NOT NULL, success INTEGER NOT NULL, attempts INTEGER NOT NULL,
            external_id TEXT, error TEXT, created_at TEXT NOT NULL)""")
        self.connection.commit()

    def add(self, record: DeliveryRecord) -> None:
        try:
            self.connection.execute(
                """INSERT INTO delivery_history(article_id,destination,success,attempts,external_id,error,created_at)
                   VALUES(?,?,?,?,?,?,?)
                   ON CONFLICT(article_id,destination) DO UPDATE SET
                     success=excluded.success, attempts=excluded.attempts,
                     external_id=excluded.external_id, error=excluded.error,
                     created_at=excluded.created_at""",
                (
                    record.article_id,
                    record.destination,
                    int(record.success),
                    record.attempts,
                    record.external_id,
                    record.error,
                    record.created_at.isoformat(),
                ),
            )
        except sqlite3.OperationalError:
            self.connection.execute(
                """INSERT OR REPLACE INTO delivery_history(article_id,destination,success,attempts,external_id,error,created_at)
                   VALUES(?,?,?,?,?,?,?)""",
                (
                    record.article_id,
                    record.destination,
                    int(record.success),
                    record.attempts,
                    record.external_id,
                    record.error,
                    record.created_at.isoformat(),
                ),
            )
        self.connection.commit()

    def all(self) -> tuple[DeliveryRecord, ...]:
        rows = self.connection.execute(
            "SELECT article_id,destination,success,attempts,external_id,error,created_at FROM delivery_history ORDER BY rowid"
        ).fetchall()
        return tuple(self._record(row) for row in rows)

    def for_article(self, article_id: str) -> tuple[DeliveryRecord, ...]:
        rows = self.connection.execute(
            "SELECT article_id,destination,success,attempts,external_id,error,created_at FROM delivery_history WHERE article_id=? ORDER BY rowid",
            (article_id,),
        ).fetchall()
        return tuple(self._record(row) for row in rows)

    @staticmethod
    def _record(row) -> DeliveryRecord:
        return DeliveryRecord(
            row[0], row[1], bool(row[2]), row[3], row[4], row[5], datetime.fromisoformat(row[6])
        )


class SQLiteIdempotencyStore:
    """Durable destination idempotency keys on the shared SQLite database."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS idempotency_keys (key TEXT PRIMARY KEY)"
        )
        self.connection.commit()

    def seen(self, key: str) -> bool:
        return (
            self.connection.execute("SELECT 1 FROM idempotency_keys WHERE key=?", (key,)).fetchone()
            is not None
        )

    def mark(self, key: str) -> None:
        self.connection.execute("INSERT OR IGNORE INTO idempotency_keys(key) VALUES(?)", (key,))
        self.connection.commit()


class SQLitePublicationQueue:
    """SQLite repository for publication queue jobs."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS publication_queue (
                id TEXT PRIMARY KEY,
                article_id TEXT NOT NULL,
                destination TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER NOT NULL,
                priority_level TEXT NOT NULL,
                source TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                last_error TEXT,
                lease_expires_at TEXT,
                next_attempt_at TEXT,
                created_at TEXT NOT NULL
            )"""
        )
        self.connection.commit()

    def add_job(self, job: PublicationJob) -> None:
        self.connection.execute(
            """INSERT INTO publication_queue (
                id, article_id, destination, status, priority, priority_level, source,
                attempts, max_attempts, last_error, lease_expires_at, next_attempt_at, created_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 status=excluded.status,
                 attempts=excluded.attempts,
                 last_error=excluded.last_error,
                 lease_expires_at=excluded.lease_expires_at,
                 next_attempt_at=excluded.next_attempt_at""",
            (
                job.id,
                job.article_id,
                job.destination,
                job.status,
                job.priority,
                job.priority_level,
                job.source,
                job.attempts,
                job.max_attempts,
                job.last_error,
                job.lease_expires_at.isoformat() if job.lease_expires_at else None,
                job.next_attempt_at.isoformat() if job.next_attempt_at else None,
                job.created_at.isoformat() if job.created_at else datetime.now(UTC).isoformat(),
            ),
        )
        self.connection.commit()

    def save_job(self, job: PublicationJob) -> None:
        self.add_job(job)

    def exists(self, job_id: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM publication_queue WHERE id = ?", (job_id,)
        ).fetchone()
        return row is not None

    def get_job(self, job_id: str) -> PublicationJob | None:
        row = self.connection.execute(
            "SELECT * FROM publication_queue WHERE id = ?", (job_id,)
        ).fetchone()
        if row is None:
            return None
        return self._to_job(row)

    def get_all_jobs(self) -> tuple[PublicationJob, ...]:
        rows = self.connection.execute(
            "SELECT * FROM publication_queue ORDER BY created_at"
        ).fetchall()
        return tuple(self._to_job(row) for row in rows)

    def get_eligible_jobs(self, now: datetime) -> tuple[PublicationJob, ...]:
        now_str = now.isoformat()
        rows = self.connection.execute(
            """SELECT * FROM publication_queue
               WHERE status IN ('pending', 'retrying')
                 AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
                 AND (lease_expires_at IS NULL OR lease_expires_at <= ?)
               ORDER BY priority DESC, created_at ASC""",
            (now_str, now_str),
        ).fetchall()
        return tuple(self._to_job(row) for row in rows)

    def get_stale_leased_jobs(self, now: datetime) -> tuple[PublicationJob, ...]:
        now_str = now.isoformat()
        rows = self.connection.execute(
            """SELECT * FROM publication_queue
               WHERE status = 'processing'
                 AND lease_expires_at IS NOT NULL
                 AND lease_expires_at <= ?""",
            (now_str,),
        ).fetchall()
        return tuple(self._to_job(row) for row in rows)

    def get_metrics(self) -> dict[str, int]:
        rows = self.connection.execute(
            "SELECT status, COUNT(*) FROM publication_queue GROUP BY status"
        ).fetchall()
        counts = {row[0]: row[1] for row in rows}

        pending = counts.get("pending", 0)
        processing = counts.get("processing", 0)
        retrying = counts.get("retrying", 0)
        dead_letter = counts.get("dead_letter", 0)
        failed = counts.get("failed", 0)
        succeeded = counts.get("succeeded", 0)

        queue_depth = pending + retrying + processing

        return {
            "queue_depth": queue_depth,
            "pending": pending,
            "processing": processing,
            "retrying": retrying,
            "dead_letter": dead_letter,
            "failed": failed + dead_letter,
            "published": succeeded,
        }

    def _to_job(self, row) -> PublicationJob:
        def parse_iso(val: str | None) -> datetime | None:
            if not val:
                return None
            dt = datetime.fromisoformat(val)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt

        return PublicationJob(
            id=row["id"],
            article_id=row["article_id"],
            destination=row["destination"],
            status=row["status"],
            priority=row["priority"],
            priority_level=row["priority_level"],
            source=row["source"],
            attempts=row["attempts"],
            max_attempts=row["max_attempts"],
            last_error=row["last_error"],
            lease_expires_at=parse_iso(row["lease_expires_at"]),
            next_attempt_at=parse_iso(row["next_attempt_at"]),
            created_at=parse_iso(row["created_at"]) or datetime.now(UTC),
        )


class SQLiteRepositories:
    """Composition point sharing one SQLite connection across all durable state."""

    def __init__(self, path: str = ":memory:") -> None:
        from yasinpress.database.delivery import SQLiteDeliveryRepository
        from yasinpress.database.jobs import SQLiteJobRepository

        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.articles = SQLiteArticleRepository(connection=self.connection)
        self.jobs = SQLiteJobRepository(self.connection)
        self.deliveries = SQLiteDeliveryRepository(self.connection)
        self.delivery_history = SQLiteDeliveryHistory(self.connection)
        self.idempotency = SQLiteIdempotencyStore(self.connection)
        self.publication_queue = SQLitePublicationQueue(self.connection)

    def close(self) -> None:
        self.connection.close()
