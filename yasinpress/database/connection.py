"""SQLite connection factory."""
import sqlite3
from pathlib import Path


def connect(path: str) -> sqlite3.Connection:
    """Open a SQLite connection with production-friendly pragmas."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection
