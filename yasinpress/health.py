from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class HealthStatus:
    ok: bool
    database: bool
    message: str


def check_database(connection: sqlite3.Connection) -> HealthStatus:
    try:
        connection.execute("SELECT 1").fetchone()
        return HealthStatus(True, True, "ok")
    except sqlite3.Error as exc:
        return HealthStatus(False, False, str(exc))
