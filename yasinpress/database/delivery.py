from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from yasinpress.publishing.history import DeliveryRecord


class SQLiteDeliveryRepository:
    """Persistent delivery history and idempotency state."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS delivery_history (
                article_id TEXT NOT NULL,
                destination TEXT NOT NULL,
                success INTEGER NOT NULL,
                attempts INTEGER NOT NULL,
                external_id TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                PRIMARY KEY (article_id, destination)
            )"""
        )
        self.connection.commit()

    def record(self, record: DeliveryRecord) -> None:
        self.connection.execute(
            """INSERT INTO delivery_history
               (article_id,destination,success,attempts,external_id,error,created_at)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(article_id,destination) DO UPDATE SET
                 success=excluded.success, attempts=excluded.attempts,
                 external_id=excluded.external_id, error=excluded.error,
                 created_at=excluded.created_at""",
            (record.article_id, record.destination, int(record.success), record.attempts,
             record.external_id, record.error, record.created_at.isoformat()),
        )
        self.connection.commit()

    def get(self, article_id: str, destination: str) -> DeliveryRecord | None:
        row = self.connection.execute(
            "SELECT * FROM delivery_history WHERE article_id=? AND destination=?",
            (article_id, destination),
        ).fetchone()
        if row is None:
            return None
        return DeliveryRecord(
            article_id=row["article_id"], destination=row["destination"],
            success=bool(row["success"]), attempts=row["attempts"],
            external_id=row["external_id"], error=row["error"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def delivered(self, article_id: str, destination: str) -> bool:
        record = self.get(article_id, destination)
        return bool(record and record.success)
