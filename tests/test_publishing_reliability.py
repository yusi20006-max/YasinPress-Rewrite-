from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.publishing import Publisher, PublishResult
from yasinpress.publishing.history import DeliveryRecord, InMemoryDeliveryHistory
from yasinpress.publishing.reliability import ReliablePublisher, RetryPolicy


class FlakyPublisher(Publisher):
    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    @property
    def name(self) -> str:
        return "flaky"

    def publish(self, article: Article) -> PublishResult:
        self.calls += 1
        if self.calls <= self.failures:
            return PublishResult(False, self.name, external_id=article.id, error="temporary")
        return PublishResult(True, self.name, external_id=article.id)


def article() -> Article:
    return Article("1", "title", "https://example.com", "content", "test", datetime.now(UTC))


def test_reliable_publisher_retries_until_success():
    publisher = FlakyPublisher(2)
    result = ReliablePublisher(
        publisher, RetryPolicy(max_attempts=3), sleeper=lambda _: None
    ).publish(article())
    assert result.success
    assert publisher.calls == 3


def test_delivery_history_filters_by_article():
    history = InMemoryDeliveryHistory()
    history.add(DeliveryRecord("1", "rss", True, 1))
    history.add(DeliveryRecord("2", "pwa", False, 3, error="failed"))
    assert len(history.for_article("1")) == 1
    assert len(history.all()) == 2
