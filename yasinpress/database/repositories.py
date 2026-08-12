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

    def save(self, article: Article) -> None:
        """Insert or replace an article."""
        self.connection.execute(
            "INSERT OR REPLACE INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                article.id,
                article.title,
                article.url,
                article.content,
                article.source,
                article.published_at.isoformat(),
                article.category,
            ),
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
