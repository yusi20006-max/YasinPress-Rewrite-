import sqlite3
from datetime import UTC, datetime

from yasinpress.database.models import Article, PublicationJob
from yasinpress.publishing import PublishResult
from yasinpress.publishing.orchestrator import PublishingOrchestrator
from yasinpress.publishing.queue import SQLitePublicationQueueEngine


class Publisher:
    name = "pwa"

    def __init__(self) -> None:
        self.calls = 0

    def publish(self, article: Article) -> PublishResult:
        self.calls += 1
        return PublishResult(True, self.name, external_id=f"remote-{self.calls}")


def test_direct_and_queued_paths_republish_the_same_updated_version():
    published = datetime(2026, 8, 15, 10, tzinfo=UTC)
    updated = datetime(2026, 8, 15, 11, tzinfo=UTC)
    first = Article(
        id="parity",
        title="نسخه اول",
        url="https://example.com/parity",
        content="اول",
        source="test",
        published_at=published,
    )
    second = Article(
        id="parity",
        title="نسخه دوم",
        url="https://example.com/parity",
        content="دوم",
        source="test",
        published_at=published,
        updated_at=updated,
    )

    direct_publisher = Publisher()
    direct = PublishingOrchestrator([direct_publisher])
    assert direct.publish(first).success_count == 1
    assert direct.publish(second).success_count == 1
    assert direct.publish(second).skipped_count == 1
    assert direct_publisher.calls == 2

    connection = sqlite3.connect(":memory:")
    engine = SQLitePublicationQueueEngine(connection)
    engine.repositories.articles.save(first)
    engine.enqueue(
        PublicationJob(
            id="parity:pwa",
            article_id="parity",
            destination="pwa",
            status="pending",
            priority=10,
            priority_level="normal",
            source="test",
        )
    )

    store = type("Store", (), {"get": lambda self, article_id: engine.repositories.articles.get(article_id), "save": engine.repositories.articles.save})()
    queued_publisher = Publisher()
    assert engine.run_once({"pwa": queued_publisher}, store, now=published).success

    engine.repositories.articles.save(second)
    engine.enqueue(
        PublicationJob(
            id="parity:pwa",
            article_id="parity",
            destination="pwa",
            status="pending",
            priority=10,
            priority_level="normal",
            source="test",
        )
    )
    assert engine.run_once({"pwa": queued_publisher}, store, now=updated).success

    engine.enqueue(
        PublicationJob(
            id="parity:pwa",
            article_id="parity",
            destination="pwa",
            status="pending",
            priority=10,
            priority_level="normal",
            source="test",
        )
    )
    assert engine.run_once({"pwa": queued_publisher}, store, now=updated).skipped
    assert queued_publisher.calls == 2
