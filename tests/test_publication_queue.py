import sqlite3
from datetime import UTC, datetime, timedelta

from yasinpress.database.models import Article, PublicationJob
from yasinpress.publishing import PublishResult
from yasinpress.publishing.queue import QueueConfig, SQLitePublicationQueueEngine


def make_job(i: int, source: str, priority: int = 10, level: str = "normal") -> PublicationJob:
    return PublicationJob(
        id=f"a{i}:eitaa", article_id=f"a{i}", destination="eitaa",
        status="pending", priority=priority, priority_level=level, source=source,
    )


def test_global_limit_is_ten_per_rolling_hour():
    db = sqlite3.connect(":memory:")
    q = SQLitePublicationQueueEngine(db)
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    for i in range(10):
        q.enqueue(make_job(i, f"s{i}"))
        job = q.claim_next(now)
        assert job is not None
        q.mark_success(job.id, now=now)
    q.enqueue(make_job(11, "s11"))
    assert q.claim_next(now) is None
    assert q.metrics(now)["published_last_hour"] == 10
    assert q.metrics(now)["remaining_global_capacity"] == 0


def test_global_capacity_opens_after_rolling_hour():
    db = sqlite3.connect(":memory:")
    q = SQLitePublicationQueueEngine(db)
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    for i in range(10):
        q.enqueue(make_job(i, f"s{i}"))
        job = q.claim_next(now)
        assert job is not None
        q.mark_success(job.id, now=now)
    q.enqueue(make_job(11, "s11"))
    assert q.claim_next(now + timedelta(hours=1, seconds=1)) is not None


def test_source_limit_is_five():
    db = sqlite3.connect(":memory:")
    q = SQLitePublicationQueueEngine(db)
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    for i in range(6):
        q.enqueue(make_job(i, "same"))
    for _ in range(5):
        job = q.claim_next(now)
        assert job is not None
        q.mark_success(job.id, now=now)
    assert q.claim_next(now) is None


def test_fair_scheduling_alternates_sources():
    db = sqlite3.connect(":memory:")
    q = SQLitePublicationQueueEngine(db, QueueConfig(global_limit=30, source_limit=5))
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    for i in range(3):
        q.enqueue(make_job(i, "alpha"))
        q.enqueue(make_job(i + 10, "beta"))
    sources = []
    for _ in range(6):
        job = q.claim_next(now)
        assert job is not None
        sources.append(job.source)
        q.mark_success(job.id, now=now)
    assert sources == ["alpha", "beta", "alpha", "beta", "alpha", "beta"]


def test_priority_is_strict_before_fairness():
    db = sqlite3.connect(":memory:")
    q = SQLitePublicationQueueEngine(db)
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    q.enqueue(make_job(1, "alpha", priority=100, level="breaking"))
    q.enqueue(make_job(2, "beta", priority=10, level="normal"))
    job = q.claim_next(now)
    assert job is not None
    assert job.priority_level == "breaking"


def test_retry_backoff_and_dead_letter():
    db = sqlite3.connect(":memory:")
    q = SQLitePublicationQueueEngine(db, QueueConfig(retry_base=timedelta(seconds=10), max_attempts=2))
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    q.enqueue(make_job(1, "source"))
    job = q.claim_next(now)
    assert job is not None
    retry = q.mark_failure(job.id, "temporary", now=now)
    assert retry.status == "retrying"
    assert retry.next_attempt_at == now + timedelta(seconds=10)
    job = q.claim_next(now + timedelta(seconds=10))
    assert job is not None
    dead = q.mark_failure(job.id, "permanent", now=now + timedelta(seconds=10))
    assert dead.status == "dead_letter"


def test_expired_lease_recovers_after_restart():
    db = sqlite3.connect(":memory:")
    q1 = SQLitePublicationQueueEngine(db, QueueConfig(lease=timedelta(seconds=5)))
    start = datetime(2026, 1, 1, 12, tzinfo=UTC)
    q1.enqueue(make_job(1, "source"))
    job = q1.claim_next(start)
    assert job is not None

    q2 = SQLitePublicationQueueEngine(db, QueueConfig(lease=timedelta(seconds=5)))
    recovered = q2.recover_expired_leases(start + timedelta(seconds=6))
    assert recovered == 1
    assert q2.get(job.id).status == "retrying"


def test_queue_persists_across_engine_restart():
    db = sqlite3.connect(":memory:")
    q1 = SQLitePublicationQueueEngine(db)
    q1.enqueue(make_job(1, "source"))
    q2 = SQLitePublicationQueueEngine(db)
    assert q2.get("a1:eitaa") is not None
    assert q2.get("a1:eitaa").status == "pending"


def test_run_once_publishes_outside_ingestion_loop():
    db = sqlite3.connect(":memory:")
    q = SQLitePublicationQueueEngine(db)
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    q.enqueue(make_job(1, "source"))
    article = Article(
        id="a1", title="title", url="https://example.test/a1", content="content", source="source"
    )

    class Store:
        def get(self, article_id: str):
            return article if article_id == "a1" else None

    class Publisher:
        name = "eitaa"

        def publish(self, received):
            assert received.id == "a1"
            return PublishResult(True, self.name, external_id="remote-1")

    result = q.run_once({"eitaa": Publisher()}, Store(), now=now)
    assert result is not None and result.success
    assert q.get("a1:eitaa").status == "succeeded"
    assert q.metrics(now)["published_last_hour"] == 1
