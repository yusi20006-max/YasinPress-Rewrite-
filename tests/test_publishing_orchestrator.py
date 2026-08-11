from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.publishing import Publisher, PublishResult
from yasinpress.publishing.orchestrator import PublishingOrchestrator


class GoodPublisher(Publisher):
    @property
    def name(self) -> str:
        return "good"

    def publish(self, article: Article) -> PublishResult:
        return PublishResult(True, self.name, external_id=article.id)


class FailingPublisher(Publisher):
    @property
    def name(self) -> str:
        return "failing"

    def publish(self, article: Article) -> PublishResult:
        raise RuntimeError("destination unavailable")


def article() -> Article:
    return Article(
        id="1",
        title="خبر",
        url="https://example.com/1",
        content="محتوا",
        source="test",
        published_at=datetime.now(UTC),
    )


def test_one_publisher_failure_does_not_block_other_destinations():
    report = PublishingOrchestrator([FailingPublisher(), GoodPublisher()]).publish(article())
    assert len(report.results) == 2
    assert not report.results[0].success
    assert report.results[1].success
    assert report.success_count == 1
