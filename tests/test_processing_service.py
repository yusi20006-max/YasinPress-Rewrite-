from datetime import UTC, datetime, timedelta

from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.database.models import Article
from yasinpress.pipeline.service import ProcessingService
from yasinpress.publishing import Publisher, PublishResult
from yasinpress.sources.feed import FeedItem


class MockAI(AIProvider):
    def __init__(self) -> None:
        self.calls = 0

    @property
    def name(self) -> str:
        return "mock"

    def enrich(self, article: Article) -> AIResult:
        self.calls += 1
        return AIResult(article.title + " AI", article.content + " enriched", self.name)


class MockPublisher(Publisher):
    @property
    def name(self) -> str:
        return "mock-publisher"

    def publish(self, article: Article) -> PublishResult:
        return PublishResult(True, self.name, article.id)


def test_processing_service_runs_ai_and_publishes_all_articles():
    items = [
        FeedItem("one", "https://example.com/1", "body", datetime.now(UTC)),
        FeedItem("two", "https://example.com/2", "body", datetime.now(UTC)),
    ]
    report = ProcessingService(source="test", ai=MockAI(), publishers=[MockPublisher()]).process(
        items
    )
    assert report.pipeline.processed == 2
    assert [a.title for a in report.pipeline.articles] == ["one AI", "two AI"]
    assert len(report.publications.results) == 2
    assert report.publications.success_count == 2


def test_stale_articles_are_rejected_before_ai_enrichment():
    ai = MockAI()
    stale = FeedItem(
        "stale",
        "https://example.com/stale",
        "old body",
        datetime.now(UTC) - timedelta(hours=13),
    )
    report = ProcessingService(source="test", ai=ai, publishers=[MockPublisher()]).process([stale])

    assert report.old_count == 1
    assert ai.calls == 0
    assert report.publications.results == ()


def test_timestamp_unknown_articles_are_rejected_before_ai_enrichment():
    ai = MockAI()
    unknown = FeedItem(
        "unknown",
        "https://example.com/unknown",
        "body",
        None,
    )
    report = ProcessingService(source="test", ai=ai, publishers=[MockPublisher()]).process([unknown])

    assert report.old_count == 1
    assert ai.calls == 0
    assert report.publications.results == ()


def test_updated_article_is_fresh_and_reprocessed():
    ai = MockAI()
    published = datetime.now(UTC) - timedelta(hours=11)
    updated = published + timedelta(hours=1)
    item = FeedItem(
        "updated",
        "https://example.com/updated",
        "body",
        published,
        updated_at=updated,
    )

    report = ProcessingService(source="test", ai=ai, publishers=[MockPublisher()]).process([item])

    assert report.old_count == 0
    assert ai.calls == 1
    assert report.pipeline.articles[0].updated_at == updated
    assert report.pipeline.articles[0].processed_at is not None


def test_freshness_gate_preserves_fetched_and_processing_metadata():
    fetched = datetime.now(UTC) - timedelta(minutes=5)
    published = fetched - timedelta(minutes=1)
    item = FeedItem(
        "metadata",
        "https://example.com/metadata",
        "body",
        published,
        fetched_at=fetched,
    )

    report = ProcessingService(source="test", publishers=[]).process([item])
    article = report.pipeline.articles[0]

    assert article.fetched_at == fetched
    assert article.received_at == fetched
    assert article.processed_at is not None
    assert article.lifecycle_state == "fetched"
