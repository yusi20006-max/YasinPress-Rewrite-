import sqlite3
from datetime import UTC, datetime, timedelta
from inspect import signature

from yasinpress.database.models import PublicationJob
from yasinpress.pipeline.application import YasinPressApplication
from yasinpress.pipeline.service import ProcessingService
from yasinpress.publishing.queue import QueueConfig, SQLitePublicationQueueEngine


def make_job(name: str, source: str, priority: int = 10) -> PublicationJob:
    return PublicationJob(
        id=f"{name}:eitaa", article_id=name, destination="eitaa", status="pending",
        priority=priority, priority_level="normal", source=source,
    )


def test_default_publication_cap_is_ten_across_application_paths():
    assert QueueConfig().global_limit == 10
    assert signature(YasinPressApplication).parameters["max_publications_per_hour"].default == 10
    assert signature(ProcessingService).parameters["max_publications_per_hour"].default == 10


def test_persistent_queue_survives_new_engine_instance():
    db = sqlite3.connect(":memory:")
    first = SQLitePublicationQueueEngine(db)
    first.enqueue(make_job("a", "source-a"))
    second = SQLitePublicationQueueEngine(db)
    claimed = second.claim_next(datetime(2026, 1, 1, tzinfo=UTC))
    assert claimed is not None
    assert claimed.article_id == "a"


def test_global_and_per_source_limits_are_reserved_before_publish():
    db = sqlite3.connect(":memory:")
    engine = SQLitePublicationQueueEngine(db, QueueConfig(global_limit=10, source_limit=5))
    now = datetime(2026, 1, 1, tzinfo=UTC)
    for i in range(6): engine.enqueue(make_job(f"a{i}", "a"))
    for i in range(6): engine.enqueue(make_job(f"b{i}", "b"))
    selected = []
    for _ in range(10):
        job = engine.claim_next(now)
        assert job is not None
        selected.append(job.source)
    assert selected.count("a") == 5
    assert selected.count("b") == 5
    assert engine.claim_next(now) is None


def test_expired_lease_is_recoverable():
    db = sqlite3.connect(":memory:")
    engine = SQLitePublicationQueueEngine(db)
    now = datetime(2026, 1, 1, tzinfo=UTC)
    engine.enqueue(make_job("a", "a"))
    job = engine.claim_next(now)
    assert job is not None
    assert job.status == "processing"
    recovered = engine.recover_expired_leases(now + timedelta(minutes=11))
    assert recovered == 1
    assert engine.get(job.id).status == "retrying"


def test_retry_backoff_and_dead_letter():
    db = sqlite3.connect(":memory:")
    engine = SQLitePublicationQueueEngine(db, QueueConfig(max_attempts=2, retry_base=timedelta(seconds=10)))
    now = datetime(2026, 1, 1, tzinfo=UTC)
    engine.enqueue(make_job("a", "a"))
    job = engine.claim_next(now)
    assert job is not None
    retry = engine.mark_failure(job.id, "temporary", now=now)
    assert retry.status == "retrying"
    retry = engine.claim_next(now + timedelta(seconds=10))
    assert retry is not None
    dead = engine.mark_failure(retry.id, "fatal", now=now + timedelta(seconds=10))
    assert dead.status == "dead_letter"


def test_priority_is_applied_before_fair_source_rotation():
    db = sqlite3.connect(":memory:")
    engine = SQLitePublicationQueueEngine(db)
    now = datetime(2026, 1, 1, tzinfo=UTC)
    engine.enqueue(make_job("normal", "a", 10))
    engine.enqueue(make_job("urgent", "b", 20))
    claimed = engine.claim_next(now)
    assert claimed is not None
    assert claimed.article_id == "urgent"
