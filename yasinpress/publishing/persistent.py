from __future__ import annotations

import sqlite3
from datetime import datetime

from yasinpress.publishing.history import DeliveryRecord


class SQLiteDeliveryHistory:
    """SQLite-backed delivery history sharing the application's database connection."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS delivery_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                destination TEXT NOT NULL,
                success INTEGER NOT NULL,
                attempts INTEGER NOT NULL,
                external_id TEXT,
                error TEXT,
                created_at TEXT NOT NULL
            )"""
        )
        self.connection.commit()

    def add(self, record: DeliveryRecord) -> None:
        self.connection.execute(
            "INSERT INTO delivery_history(article_id,destination,success,attempts,external_id,error,created_at) VALUES(?,?,?,?,?,?,?)",
            (record.article_id, record.destination, int(record.success), record.attempts,
             record.external_id, record.error, record.created_at.isoformat()),
        )
        self.connection.commit()

    def all(self) -> tuple[DeliveryRecord, ...]:
        rows = self.connection.execute("SELECT article_id,destination,success,attempts,external_id,error,created_at FROM delivery_history ORDER BY id").fetchall()
        return tuple(DeliveryRecord(r[0], r[1], bool(r[2]), r[3], r[4], r[5], datetime.fromisoformat(r[6])) for r in rows)

    def for_article(self, article_id: str) -> tuple[DeliveryRecord, ...]:
        rows = self.connection.execute("SELECT article_id,destination,success,attempts,external_id,error,created_at FROM delivery_history WHERE article_id=? ORDER BY id", (article_id,)).fetchall()
        return tuple(DeliveryRecord(r[0], r[1], bool(r[2]), r[3], r[4], r[5], datetime.fromisoformat(r[6])) for r in rows)


class SQLiteIdempotencyStore:
    """SQLite-backed idempotency keys."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.execute("CREATE TABLE IF NOT EXISTS idempotency_keys (key TEXT PRIMARY KEY)")
        self.connection.commit()

    def seen(self, key: str) -> bool:
        return self.connection.execute("SELECT 1 FROM idempotency_keys WHERE key=?", (key,)).fetchone() is not None

    def mark(self, key: str) -> None:
        self.connection.execute("INSERT OR IGNORE INTO idempotency_keys(key) VALUES(?)", (key,))
        self.connection.commit()
