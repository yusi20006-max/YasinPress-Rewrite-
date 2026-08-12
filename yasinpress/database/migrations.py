"""Database migrations."""

import sqlite3

MIGRATIONS: tuple[str, ...] = (
    """CREATE TABLE IF NOT EXISTS articles (
        id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL UNIQUE,
        content TEXT NOT NULL, source TEXT NOT NULL, published_at TEXT NOT NULL,
        category TEXT
    )""",
    """ALTER TABLE articles ADD COLUMN event_id TEXT""",
    """ALTER TABLE articles ADD COLUMN received_at TEXT""",
    """ALTER TABLE articles ADD COLUMN lifecycle_state TEXT""",
    """ALTER TABLE articles ADD COLUMN ai_state TEXT""",
    """ALTER TABLE articles ADD COLUMN ai_error TEXT""",
    """ALTER TABLE articles ADD COLUMN source_metadata TEXT""",
)


def migrate(connection: sqlite3.Connection) -> None:
    """Apply idempotent migrations."""
    for statement in MIGRATIONS:
        try:
            connection.execute(statement)
        except sqlite3.OperationalError:
            pass
    connection.commit()
