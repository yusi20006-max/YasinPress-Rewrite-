"""SQLite backup support."""

import sqlite3
from pathlib import Path


def backup_database(source: str, destination: str) -> None:
    """Copy a SQLite database using the online backup API."""
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)
