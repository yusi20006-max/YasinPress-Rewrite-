from datetime import datetime, timezone
import sqlite3

from yasinpress.publishing.history import DeliveryRecord
from yasinpress.publishing.sqlite_state import SQLiteDeliveryHistory, SQLiteIdempotencyStore


def test_sqlite_idempotency_survives_new_adapter():
    conn = sqlite3.connect(":memory:")
    first = SQLiteIdempotencyStore(conn)
    assert first.claim("article:pwa") is True
    second = SQLiteIdempotencyStore(conn)
    assert second.seen("article:pwa") is True
    assert second.claim("article:pwa") is False


def test_sqlite_delivery_history_round_trip():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    history = SQLiteDeliveryHistory(conn)
    history.add(DeliveryRecord("article", "rss", True, 1, created_at=datetime.now(timezone.utc)))
    assert len(history.for_article("article")) == 1
