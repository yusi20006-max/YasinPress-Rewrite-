"""Repository implementations."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime

from .models import Article


class ArticleRepository:
    """SQLite repository for articles and operational counters."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("""CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL,
            content TEXT NOT NULL, source TEXT NOT NULL,
            published_at TEXT, category TEXT,
            event_id TEXT, received_at TEXT, lifecycle_state TEXT,
            ai_state TEXT, ai_error TEXT, source_metadata TEXT)""")
        for column in [
            "event_id",
            "received_at",
            "lifecycle_state",
            "ai_state",
            "ai_error",
            "source_metadata",
            "updated_at",
            "fetched_at",
            "processed_at",
            "published_to_channel_at",
        ]:
            try:
                self.connection.execute(f"ALTER TABLE articles ADD COLUMN {column} TEXT")
            except sqlite3.OperationalError:
                pass

        # Schema migration to make published_at nullable on legacy databases
        cursor = self.connection.execute("PRAGMA table_info(articles)")
        columns_info = cursor.fetchall()
        published_at_notnull = False
        for col in columns_info:
            if col["name"] == "published_at" and int(col["notnull"]) == 1:
                published_at_notnull = True
                break

        if published_at_notnull:
            try:
                self.connection.execute("BEGIN IMMEDIATE")
                self.connection.execute("""CREATE TABLE articles_backup (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL,
                    content TEXT NOT NULL, source TEXT NOT NULL,
                    published_at TEXT, category TEXT,
                    event_id TEXT, received_at TEXT, lifecycle_state TEXT,
                    ai_state TEXT, ai_error TEXT, source_metadata TEXT,
                    updated_at TEXT, fetched_at TEXT, processed_at TEXT,
                    published_to_channel_at TEXT)""")
                existing_column_names = [col["name"] for col in columns_info]
                cols_str = ", ".join(existing_column_names)
                self.connection.execute(f"INSERT INTO articles_backup ({cols_str}) SELECT {cols_str} FROM articles")
                self.connection.execute("DROP TABLE articles")
                self.connection.execute("ALTER TABLE articles_backup RENAME TO articles")
                self.connection.execute("COMMIT")
            except Exception:
                self.connection.execute("ROLLBACK")
                raise

        self.connection.commit()

    def save(self, article: Article) -> None:
        """Insert or replace an article."""
        import json
        metadata_str = json.dumps(article.source_metadata if article.source_metadata is not None else {})
        self.connection.execute(
            """INSERT INTO articles(
                id, title, url, content, source, published_at, category,
                event_id, received_at, lifecycle_state, ai_state, ai_error, source_metadata,
                updated_at, fetched_at, processed_at, published_to_channel_at
               )
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
               title=excluded.title, url=excluded.url, content=excluded.content,
               source=excluded.source, published_at=excluded.published_at, category=excluded.category,
               event_id=excluded.event_id, received_at=excluded.received_at, lifecycle_state=excluded.lifecycle_state,
               ai_state=excluded.ai_state, ai_error=excluded.ai_error, source_metadata=excluded.source_metadata,
               updated_at=excluded.updated_at, fetched_at=excluded.fetched_at, processed_at=excluded.processed_at,
               published_to_channel_at=excluded.published_to_channel_at""",
            (
                article.id,
                article.title,
                article.url,
                article.content,
                article.source,
                article.published_at.isoformat() if article.published_at else None,
                article.category,
                article.event_id,
                article.received_at.isoformat() if article.received_at else None,
                article.lifecycle_state,
                article.ai_state,
                article.ai_error,
                metadata_str,
                article.updated_at.isoformat() if article.updated_at else None,
                article.fetched_at.isoformat() if article.fetched_at else None,
                article.processed_at.isoformat() if article.processed_at else None,
                article.published_to_channel_at.isoformat() if article.published_to_channel_at else None,
            ),
        )
        self.connection.commit()

    def get(self, article_id: str) -> Article | None:
        row = self.connection.execute("SELECT * FROM articles WHERE id=? OR url=? LIMIT 1", (article_id, article_id)).fetchone()
        return self._row_to_article(row) if row else None

    @staticmethod
    def _row_to_article(row) -> Article:
        import json
        def dt(name: str, default: datetime | None = None) -> datetime | None:
            try:
                value = row[name]
            except (IndexError, KeyError):
                return default
            if not value:
                return default
            parsed = datetime.fromisoformat(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

        meta_val = row["source_metadata"]
        try:
            source_meta = json.loads(meta_val) if meta_val else {}
        except Exception:
            source_meta = {}

        return Article(
            id=row["id"], title=row["title"], url=row["url"], content=row["content"], source=row["source"],
            published_at=dt("published_at", None), category=row["category"], event_id=row["event_id"],
            received_at=dt("received_at", datetime.now(UTC)) or datetime.now(UTC), lifecycle_state=row["lifecycle_state"] or "fetched",
            ai_state=row["ai_state"] or "none", ai_error=row["ai_error"], source_metadata=source_meta,
            updated_at=dt("updated_at", None),
            fetched_at=dt("fetched_at", datetime.now(UTC)) or datetime.now(UTC),
            processed_at=dt("processed_at", None),
            published_to_channel_at=dt("published_to_channel_at", None),
        )

    def exists(self, article_id: str) -> bool:
        """Return whether an article exists."""
        row = self.connection.execute(
            "SELECT 1 FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
        return row is not None

    def count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) FROM articles").fetchone()
        return int(row[0]) if row else 0

    def save_operational_report(self, report: dict[str, object]) -> None:
        """Persist an hourly report snapshot for PWA/API consumers."""
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS operational_reports (
                timestamp TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        import json

        timestamp = str(report.get("timestamp") or datetime.now(UTC).isoformat())
        self.connection.execute(
            "INSERT OR REPLACE INTO operational_reports(timestamp, payload) VALUES (?, ?)",
            (timestamp, json.dumps(report, ensure_ascii=False, sort_keys=True)),
        )
        self.connection.commit()

    def recent_operational_reports(self, limit: int = 24) -> Iterable[dict[str, object]]:
        """Return the latest persisted hourly reports, newest first."""
        import json

        rows = self.connection.execute(
            "SELECT payload FROM operational_reports ORDER BY timestamp DESC LIMIT ?",
            (max(1, limit),),
        ).fetchall()
        return (json.loads(row[0]) for row in rows)
