from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime

from yasinpress.database.models import Article
from yasinpress.publishing.history import DeliveryRecord


class SQLiteArticleRepository:
    """Persistence adapter for normalized Article records."""

    def __init__(self, path: str = ":memory:", connection: sqlite3.Connection | None = None) -> None:
        self._owns_connection = connection is None
        self.connection = connection or sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("""CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL,
            content TEXT NOT NULL, source TEXT NOT NULL,
            published_at TEXT NOT NULL, category TEXT)""")
        self.connection.commit()

    def save(self, article: Article) -> None:
        self.connection.execute(
            """INSERT INTO articles(id,title,url,content,source,published_at,category)
               VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
               title=excluded.title,url=excluded.url,content=excluded.content,
               source=excluded.source,published_at=excluded.published_at,category=excluded.category""",
            (article.id, article.title, article.url, article.content, article.source,
             article.published_at.isoformat(), article.category),
        )
        self.connection.commit()

    def save_many(self, articles: Iterable[Article]) -> None:
        for article in articles:
            self.save(article)

    def get(self, article_id: str) -> Article | None:
        row = self.connection.execute(
            "SELECT * FROM articles WHERE id=? OR url=? LIMIT 1", (article_id, article_id)
        ).fetchone()
        if row is None:
            return None
        return Article(row["id"], row["title"], row["url"], row["content"], row["source"], datetime.fromisoformat(row["published_at"]), row["category"])

    def all(self) -> tuple[Article, ...]:
        rows = self.connection.execute("SELECT * FROM articles ORDER BY published_at DESC").fetchall()
        return tuple(Article(r["id"], r["title"], r["url"], r["content"], r["source"], datetime.fromisoformat(r["published_at"]), r["category"]) for r in rows)

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
        self.connection.execute(
            "INSERT INTO delivery_history(article_id,destination,success,attempts,external_id,error,created_at) VALUES(?,?,?,?,?,?,?)",
            (record.article_id, record.destination, int(record.success), record.attempts, record.external_id, record.error, record.created_at.isoformat()),
        )
        self.connection.commit()

    def all(self) -> tuple[DeliveryRecord, ...]:
        rows = self.connection.execute("SELECT article_id,destination,success,attempts,external_id,error,created_at FROM delivery_history ORDER BY rowid").fetchall()
        return tuple(self._record(row) for row in rows)

    def for_article(self, article_id: str) -> tuple[DeliveryRecord, ...]:
        rows = self.connection.execute("SELECT article_id,destination,success,attempts,external_id,error,created_at FROM delivery_history WHERE article_id=? ORDER BY rowid", (article_id,)).fetchall()
        return tuple(self._record(row) for row in rows)

    @staticmethod
    def _record(row) -> DeliveryRecord:
        return DeliveryRecord(row[0], row[1], bool(row[2]), row[3], row[4], row[5], datetime.fromisoformat(row[6]))


class SQLiteIdempotencyStore:
    """Durable destination idempotency keys on the shared SQLite database."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.execute("CREATE TABLE IF NOT EXISTS idempotency_keys (key TEXT PRIMARY KEY)")
        self.connection.commit()

    def seen(self, key: str) -> bool:
        return self.connection.execute("SELECT 1 FROM idempotency_keys WHERE key=?", (key,)).fetchone() is not None

    def mark(self, key: str) -> None:
        self.connection.execute("INSERT OR IGNORE INTO idempotency_keys(key) VALUES(?)", (key,))
        self.connection.commit()


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

    def close(self) -> None:
        self.connection.close()
