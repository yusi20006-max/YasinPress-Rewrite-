from datetime import datetime, timezone

from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.database.models import Article
from yasinpress.pipeline.service import ProcessingService
from yasinpress.publishing import PublishResult, Publisher
from yasinpress.sources.feed import FeedItem


class MockAI(AIProvider):
    @property
    def name(self) -> str:
        return "mock"

    def enrich(self, article: Article) -> AIResult:
        return AIResult(article.title + " AI", article.content + " enriched", self.name)


class MockPublisher(Publisher):
    @property
    def name(self) -> str:
        return "mock-publisher"

    def publish(self, article: Article) -> PublishResult:
        return PublishResult(True, self.name, article.id)


def test_processing_service_runs_ai_and_publishes_all_articles():
    items = [
        FeedItem("one", "https://example.com/1", "body", datetime.now(timezone.utc)),
        FeedItem("two", "https://example.com/2", "body", datetime.now(timezone.utc)),
    ]
    report = ProcessingService(source="test", ai=MockAI(), publishers=[MockPublisher()]).process(items)
    assert report.pipeline.processed == 2
    assert [a.title for a in report.pipeline.articles] == ["one AI", "two AI"]
    assert len(report.publications.results) == 2
    assert report.publications.success_count == 2
