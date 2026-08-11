from __future__ import annotations

import sqlite3

from yasinpress.database.delivery import SQLiteDeliveryRepository
from yasinpress.publishing.history import DeliveryRecord


class SQLiteIdempotencyStore:
    """Durable destination-delivery key store backed by the application SQLite connection."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.execute("CREATE TABLE IF NOT EXISTS delivery_keys (key TEXT PRIMARY KEY)")
        self.connection.commit()

    def seen(self, key: str) -> bool:
        return (
            self.connection.execute("SELECT 1 FROM delivery_keys WHERE key=?", (key,)).fetchone()
            is not None
        )

    def mark(self, key: str) -> None:
        self.connection.execute("INSERT OR IGNORE INTO delivery_keys(key) VALUES(?)", (key,))
        self.connection.commit()

    def claim(self, key: str) -> bool:
        cursor = self.connection.execute(
            "INSERT OR IGNORE INTO delivery_keys(key) VALUES(?)", (key,)
        )
        self.connection.commit()
        return cursor.rowcount == 1


class SQLiteDeliveryHistory:
    """Adapter exposing persistent history through the storage-neutral history API."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.repository = SQLiteDeliveryRepository(connection)

    def add(self, record: DeliveryRecord) -> None:
        self.repository.record(record)

    def all(self) -> tuple[DeliveryRecord, ...]:
        rows = self.repository.connection.execute(
            "SELECT * FROM delivery_history ORDER BY created_at DESC"
        ).fetchall()
        return tuple(
            DeliveryRecord(
                r["article_id"],
                r["destination"],
                bool(r["success"]),
                r["attempts"],
                r["external_id"],
                r["error"],
                __import__("datetime").datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        )

    def for_article(self, article_id: str) -> tuple[DeliveryRecord, ...]:
        return tuple(r for r in self.all() if r.article_id == article_id)
