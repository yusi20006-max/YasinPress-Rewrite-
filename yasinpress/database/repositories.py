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
        """Insert or replace an article."""
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
