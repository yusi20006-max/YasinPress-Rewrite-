"""Transaction helpers."""
from contextlib import contextmanager
from collections.abc import Iterator
import sqlite3

@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run operations inside a commit-or-rollback transaction."""
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
