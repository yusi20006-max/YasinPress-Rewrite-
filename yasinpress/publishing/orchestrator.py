from __future__ import annotations

from dataclasses import dataclass

from yasinpress.database.models import Article
from yasinpress.publishing import PublishResult, Publisher
from yasinpress.publishing.history import DeliveryRecord, InMemoryDeliveryHistory
from yasinpress.publishing.idempotency import IdempotencyStore
from yasinpress.publishing.reliability import ReliablePublisher, RetryPolicy


@dataclass(frozen=True)
class PublishReport:
    results: tuple[PublishResult, ...]

    @property
    def success_count(self) -> int:
        return sum(result.success for result in self.results)

    @property
    def failure_count(self) -> int:
        return sum(not result.success for result in self.results)


class PublishingOrchestrator:
    """Coordinate independent destinations with retry, history, and idempotency."""

    def __init__(
        self,
        publishers: list[Publisher] | tuple[Publisher, ...] = (),
        *,
        retry_policy: RetryPolicy | None = None,
        history: InMemoryDeliveryHistory | None = None,
        idempotency: IdempotencyStore | None = None,
    ) -> None:
        self.publishers = tuple(ReliablePublisher(publisher, retry_policy) for publisher in publishers)
        self.history = history or InMemoryDeliveryHistory()
        self.idempotency = idempotency or IdempotencyStore()

    def publish(self, article: Article) -> PublishReport:
        results: list[PublishResult] = []
        for publisher in self.publishers:
            key = f"{article.id}:{publisher.publisher.name}"
            if self.idempotency.seen(key):
                results.append(PublishResult(True, publisher.publisher.name, external_id=article.id))
                continue

            result = publisher.publish(article)
            results.append(result)
            self.history.add(
                DeliveryRecord(
                    article_id=article.id,
                    destination=result.destination,
                    success=result.success,
                    attempts=publisher.attempts,
                    external_id=result.external_id,
                    error=result.error,
                )
            )
            if result.success:
                self.idempotency.mark(key)
        return PublishReport(tuple(results))
