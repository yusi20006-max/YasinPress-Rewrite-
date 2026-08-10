from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime

from yasinpress.database.models import Article


class SQLiteArticleRepository:
    """Persistence adapter for normalized Article records."""

    def __init__(self, path: str = ":memory:", connection: sqlite3.Connection | None = None) -> None:
        self._owns_connection = connection is None
        self.connection = connection or sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                published_at TEXT NOT NULL,
                category TEXT
            )"""
        )
        self.connection.commit()

    def save(self, article: Article) -> None:
        self.connection.execute(
            """INSERT INTO articles(id,title,url,content,source,published_at,category)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                 title=excluded.title, url=excluded.url, content=excluded.content,
                 source=excluded.source, published_at=excluded.published_at,
                 category=excluded.category""",
            (article.id, article.title, article.url, article.content, article.source,
             article.published_at.isoformat(), article.category),
        )
        self.connection.commit()

    def save_many(self, articles: Iterable[Article]) -> None:
        for article in articles:
            self.save(article)

    def get(self, article_id: str) -> Article | None:
        row = self.connection.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()
        if row is None:
            return None
        return Article(row["id"], row["title"], row["url"], row["content"], row["source"], datetime.fromisoformat(row["published_at"]), row["category"])

    def all(self) -> tuple[Article, ...]:
        rows = self.connection.execute("SELECT * FROM articles ORDER BY published_at DESC").fetchall()
        return tuple(Article(r["id"], r["title"], r["url"], r["content"], r["source"], datetime.fromisoformat(r["published_at"]), r["category"]) for r in rows)

    def close(self) -> None:
        if self._owns_connection:
            self.connection.close()
