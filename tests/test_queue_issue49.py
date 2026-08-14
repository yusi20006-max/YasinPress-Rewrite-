import sqlite3
from datetime import UTC, datetime, timedelta

from yasinpress.database.models import Article, PublicationJob
from yasinpress.publishing import PublishResult
from yasinpress.publishing.orchestrator import PublishingOrchestrator
from yasinpress.publishing.queue import QueueConfig, SQLitePublicationQueueEngine


def job(article_id: str, source: str, destination: str, created_at: datetime | None = None) -> PublicationJob:
    return PublicationJob(
        id=f"{article_id}:{destination}",
        article_id=article_id,
        destination=destination,
        status="pending",
        priority=10,
        priority_level="normal",
        source=source,
        created_at=created_at or datetime.now(UTC),
    )


def test_fanout_does_not_consume_extra_global_capacity():
    db = sqlite3.connect(":memory:")
    queue = SQLitePublicationQueueEngine(db, QueueConfig(global_limit=1, source_limit=1))
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    queue.enqueue(job("a1", "source", "eitaa", now))
    queue.enqueue(job("a1", "source", "pwa", now))

    first = queue.claim_next(now)
    assert first is not None
    queue.mark_success(first.id, now=now)

    second = queue.claim_next(now)
    assert second is not None
    assert second.article_id == "a1"
    assert second.destination != first.destination
    assert queue.metrics(now)["published_last_hour"] == 1


def test_updated_article_version_republishes_after_previous_success():
    db = sqlite3.connect(":memory:")
    queue = SQLitePublicationQueueEngine(db)
    first_time = datetime(2026, 1, 1, 12, tzinfo=UTC)
    second_time = first_time + timedelta(minutes=5)
    calls: list[str] = []

    original = Article(
        id="a1", title="original", url="https://example.test/a1", content="original",
        source="source", published_at=first_time,
    )
    queue.repositories.articles.save(original)
    queue.enqueue(job("a1", "source", "eitaa", first_time))

    class Publisher:
        name = "eitaa"

        def publish(self, article):
            calls.append(article.title)
            return PublishResult(True, self.name, external_id=article.id)

    first = queue.run_once({"eitaa": Publisher()}, queue.repositories.articles, now=first_time)
    assert first is not None and first.success

    updated = Article(
        id="a1", title="updated", url="https://example.test/a1", content="updated",
        source="source", published_at=first_time, updated_at=second_time,
        published_to_channel_at=None,
    )
    queue.repositories.articles.save(updated)
    queue.enqueue(job("a1", "source", "eitaa", second_time))

    second = queue.run_once({"eitaa": Publisher()}, queue.repositories.articles, now=second_time)
    assert second is not None and second.success
    assert calls == ["original", "updated"]
    assert queue.repositories.articles.get("a1").published_to_channel_at == second_time


def test_orchestrator_republishes_new_article_version():
    calls: list[str] = []

    class Publisher:
        name = "mock"

        def publish(self, article):
            calls.append(article.title)
            return PublishResult(True, self.name, external_id=article.id)

    orchestrator = PublishingOrchestrator([Publisher()])
    first_time = datetime(2026, 1, 1, 12, tzinfo=UTC)
    second_time = first_time + timedelta(minutes=5)
    original = Article(
        id="a1", title="original", url="https://example.test/a1", content="original",
        source="source", published_at=first_time,
    )
    updated = Article(
        id="a1", title="updated", url="https://example.test/a1", content="updated",
        source="source", published_at=first_time, updated_at=second_time,
        published_to_channel_at=None,
    )

    assert orchestrator.publish(original).success_count == 1
    assert orchestrator.publish(updated).success_count == 1
    assert calls == ["original", "updated"]
