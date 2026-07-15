"""Database migrations."""
import sqlite3

MIGRATIONS: tuple[str, ...] = (
    """CREATE TABLE IF NOT EXISTS articles (
        id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL UNIQUE,
        content TEXT NOT NULL, source TEXT NOT NULL, published_at TEXT NOT NULL,
        category TEXT
    )""",
)


def migrate(connection: sqlite3.Connection) -> None:
    """Apply idempotent migrations."""
    for statement in MIGRATIONS:
        connection.execute(statement)
    connection.commit()
