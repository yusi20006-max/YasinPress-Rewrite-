from datetime import datetime, timezone

from yasinpress.database.models import Article
from yasinpress.publishing import PublishResult, Publisher
from yasinpress.publishing.history import InMemoryDeliveryHistory
from yasinpress.publishing.idempotency import IdempotencyStore
from yasinpress.publishing.orchestrator import PublishingOrchestrator
from yasinpress.publishing.reliability import RetryPolicy


class FlakyPublisher(Publisher):
    def __init__(self, failures: int, name: str = "flaky") -> None:
        self.failures = failures
        self.calls = 0
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def publish(self, article: Article) -> PublishResult:
        self.calls += 1
        if self.calls <= self.failures:
            return PublishResult(False, self.name, external_id=article.id, error="temporary")
        return PublishResult(True, self.name, external_id=article.id)


def article() -> Article:
    return Article("1", "title", "https://example.com", "content", "test", datetime.now(timezone.utc))


def test_orchestrator_retries_and_records_attempts():
    publisher = FlakyPublisher(2)
    history = InMemoryDeliveryHistory()
    result = PublishingOrchestrator(
        [publisher],
        retry_policy=RetryPolicy(max_attempts=3),
        history=history,
        idempotency=IdempotencyStore(),
    ).publish(article())
    assert result.success_count == 1
    record = history.all()[0]
    assert record.success
    assert record.attempts == 3


def test_orchestrator_is_idempotent_after_success():
    publisher = FlakyPublisher(0)
    orchestrator = PublishingOrchestrator([publisher], retry_policy=RetryPolicy(max_attempts=1))
    assert orchestrator.publish(article()).success_count == 1
    assert orchestrator.publish(article()).success_count == 1
    assert publisher.calls == 1


def test_failed_delivery_is_retried_but_not_marked_delivered():
    publisher = FlakyPublisher(5)
    history = InMemoryDeliveryHistory()
    orchestrator = PublishingOrchestrator(
        [publisher],
        retry_policy=RetryPolicy(max_attempts=2),
        history=history,
    )
    assert orchestrator.publish(article()).failure_count == 1
    assert orchestrator.publish(article()).failure_count == 1
    assert publisher.calls == 4
    assert len(history.all()) == 2
