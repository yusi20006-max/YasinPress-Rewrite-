"""Repository implementations."""

import sqlite3
from datetime import UTC, datetime

from .models import Article


class ArticleRepository:
    """SQLite repository for articles."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("""CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL,
            content TEXT NOT NULL, source TEXT NOT NULL,
            published_at TEXT NOT NULL, category TEXT,
            event_id TEXT, received_at TEXT, lifecycle_state TEXT,
            ai_state TEXT, ai_error TEXT, source_metadata TEXT)""")
        for column in ["event_id", "received_at", "lifecycle_state", "ai_state", "ai_error", "source_metadata"]:
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
                article.published_at.isoformat() if hasattr(article.published_at, "isoformat") else article.published_at,
                article.category,
                article.event_id,
                article.received_at.isoformat() if hasattr(article.received_at, "isoformat") else article.received_at,
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
