"""Transaction helpers."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run operations inside a commit-or-rollback transaction."""
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
