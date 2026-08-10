from __future__ import annotations

import sqlite3
from datetime import datetime

from yasinpress.scheduler.jobs import Job, JobStatus


class SQLiteJobRepository:
    """Persistent scheduler job state."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                error TEXT
            )"""
        )
        self.connection.commit()

    def save(self, job: Job) -> None:
        self.connection.execute(
            """INSERT INTO jobs(id,name,status,attempts,created_at,started_at,finished_at,error)
               VALUES(?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name,status=excluded.status,attempts=excluded.attempts,
                 started_at=excluded.started_at,finished_at=excluded.finished_at,error=excluded.error""",
            (job.id, job.name, job.status.value, job.attempts, job.created_at.isoformat(),
             job.started_at.isoformat() if job.started_at else None,
             job.finished_at.isoformat() if job.finished_at else None, job.error),
        )
        self.connection.commit()

    def get(self, job_id: str) -> Job | None:
        row = self.connection.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            return None
        return Job(
            id=row["id"], name=row["name"], status=JobStatus(row["status"]),
            attempts=row["attempts"], created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
            error=row["error"],
        )
