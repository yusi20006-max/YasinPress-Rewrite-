"""Repository implementations."""

import sqlite3

from .models import Article


class ArticleRepository:
    """SQLite repository for articles."""

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
