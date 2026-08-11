import sqlite3
from datetime import UTC, datetime

from yasinpress.database.delivery import SQLiteDeliveryRepository
from yasinpress.database.jobs import SQLiteJobRepository
from yasinpress.publishing.history import DeliveryRecord
from yasinpress.runtime import Runtime
from yasinpress.scheduler.jobs import JobStatus, new_job


def test_delivery_history_round_trip():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    repo = SQLiteDeliveryRepository(conn)
    record = DeliveryRecord("a1", "pwa", True, 2, external_id="x", created_at=datetime.now(UTC))
    repo.record(record)
    assert repo.delivered("a1", "pwa")
    assert repo.get("a1", "pwa").attempts == 2


def test_job_repository_round_trip():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    repo = SQLiteJobRepository(conn)
    job = new_job("feed")
    job.status = JobStatus.SUCCEEDED
    repo.save(job)
    loaded = repo.get(job.id)
    assert loaded is not None
    assert loaded.status is JobStatus.SUCCEEDED


def test_runtime_stop_is_graceful():
    calls = []
    runtime = Runtime(lambda: (calls.append(1), runtime.stop()), interval_seconds=0.001)
    runtime.run()
    assert calls == [1]
