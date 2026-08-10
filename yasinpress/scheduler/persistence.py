from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from yasinpress.scheduler.jobs import Job, JobStatus


@dataclass(frozen=True)
class JobSnapshot:
    id: str
    name: str
    status: JobStatus
    attempts: int
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None


class InMemoryJobStore:
    """Persistence boundary for scheduler state."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobSnapshot] = {}

    def save(self, job: Job) -> JobSnapshot:
        snapshot = JobSnapshot(job.id, job.name, job.status, job.attempts, job.created_at, job.started_at, job.finished_at, job.error)
        self._jobs[job.id] = snapshot
        return snapshot

    def get(self, job_id: str) -> JobSnapshot | None:
        return self._jobs.get(job_id)

    def all(self) -> tuple[JobSnapshot, ...]:
        return tuple(self._jobs.values())


class JsonJobStore(InMemoryJobStore):
    """File-backed scheduler state adapter."""

    def __init__(self, path: str | Path) -> None:
        super().__init__()
        self.path = Path(path)
        self._load()

    def save(self, job: Job) -> JobSnapshot:
        snapshot = super().save(job)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([
            {
                "id": item.id,
                "name": item.name,
                "status": item.status.value,
                "attempts": item.attempts,
                "created_at": item.created_at.isoformat(),
                "started_at": item.started_at.isoformat() if item.started_at else None,
                "finished_at": item.finished_at.isoformat() if item.finished_at else None,
                "error": item.error,
            }
            for item in self.all()
        ], ensure_ascii=False, indent=2), encoding="utf-8")
        return snapshot

    def _load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        for item in raw:
            self._jobs[item["id"]] = JobSnapshot(
                item["id"], item["name"], JobStatus(item["status"]), item["attempts"],
                datetime.fromisoformat(item["created_at"]),
                datetime.fromisoformat(item["started_at"]) if item["started_at"] else None,
                datetime.fromisoformat(item["finished_at"]) if item["finished_at"] else None,
                item["error"],
            )
