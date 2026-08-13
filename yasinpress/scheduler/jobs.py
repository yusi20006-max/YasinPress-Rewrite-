from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


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
    result: object | None = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now(UTC)


@dataclass
class JobExecution:
    """Runtime execution record for a scheduled task."""

    name: str
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.status == JobStatus.SUCCEEDED

    def run(self, handler: Callable[[], object]) -> JobExecution:
        self.status = JobStatus.RUNNING
        self.attempts += 1
        self.started_at = datetime.now(UTC)
        try:
            handler()
        except Exception as exc:  # noqa: BLE001 - execution boundary records task failures
            self.status = JobStatus.FAILED
            self.error = str(exc)
        else:
            self.status = JobStatus.SUCCEEDED
            self.error = None
        finally:
            self.finished_at = datetime.now(UTC)
        return self


class JobRunner:
    """Small deterministic job runner; scheduling policy is intentionally separate."""

    def __init__(self, handler: Callable[[], None]) -> None:
        self.handler = handler

    def run(self, job: Job) -> Job:
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(UTC)
        job.attempts += 1
        try:
            self.handler()
        except Exception as exc:  # noqa: BLE001 - runner records arbitrary task failures
            job.status = JobStatus.FAILED
            job.error = str(exc)
        else:
            job.status = JobStatus.SUCCEEDED
            job.error = None
        finally:
            job.finished_at = datetime.now(UTC)
        return job


def new_job(name: str) -> Job:
    return Job(id=str(uuid.uuid4()), name=name)
