from __future__ import annotations

from dataclasses import dataclass

from yasinpress.database.models import Article
from yasinpress.publishing import Publisher, PublishResult
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
        return sum(not result.success and not result.skipped for result in self.results)

    @property
    def skipped_count(self) -> int:
        return sum(result.skipped for result in self.results)


class PublishingOrchestrator:
    """Coordinate independent destinations with retry, durable history, and idempotency."""

    def __init__(
        self,
        publishers: list[Publisher] | tuple[Publisher, ...] = (),
        *,
        retry_policy: RetryPolicy | None = None,
        history=None,
        idempotency=None,
    ) -> None:
        self.publishers = tuple(
            ReliablePublisher(publisher, retry_policy) for publisher in publishers
        )
        self.history = history or InMemoryDeliveryHistory()
        self.idempotency = idempotency or IdempotencyStore()

    @staticmethod
    def _version_key(article: Article, destination: str) -> str | None:
        """Return a delivery version only for an explicit article update."""
        if article.updated_at is None:
            return None
        return f"{article.id}:{destination}:version:{article.updated_at.isoformat()}"

    def publish(self, article: Article) -> PublishReport:
        results: list[PublishResult] = []
        for publisher in self.publishers:
            destination = publisher.publisher.name
            key = self._version_key(article, destination)
            legacy_key = f"{article.id}:{destination}"

            # Preserve legacy idempotency for unchanged articles. An explicit
            # updated_at creates a new delivery version while repeated retries
            # of that same version remain idempotent.
            already_published_version = key is not None and self.idempotency.seen(key)
            unchanged_legacy_delivery = key is None and self.idempotency.seen(legacy_key)
            if already_published_version or unchanged_legacy_delivery:
                results.append(
                    PublishResult(
                        True,
                        destination,
                        external_id=article.id,
                        skipped=True,
                    )
                )
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
                if key is not None:
                    self.idempotency.mark(key)
                self.idempotency.mark(legacy_key)
        return PublishReport(tuple(results))
