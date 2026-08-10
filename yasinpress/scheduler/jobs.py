from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable
import uuid


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    name: str
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    created_at: datetime = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class JobRunner:
    """Small deterministic job runner; scheduling policy is intentionally separate."""

    def __init__(self, handler: Callable[[], None]) -> None:
        self.handler = handler

    def run(self, job: Job) -> Job:
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        job.attempts += 1
        try:
            self.handler()
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
        else:
            job.status = JobStatus.SUCCEEDED
            job.error = None
        finally:
            job.finished_at = datetime.now(timezone.utc)
        return job


def new_job(name: str) -> Job:
    return Job(id=str(uuid.uuid4()), name=name)
