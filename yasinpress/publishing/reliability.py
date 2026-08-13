from __future__ import annotations

import time
from dataclasses import dataclass

from yasinpress.database.models import Article
from yasinpress.publishing import Publisher, PublishResult


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.25
    max_delay_seconds: float = 5.0

    def delay(self, attempt: int) -> float:
        return min(self.base_delay_seconds * (2 ** max(0, attempt - 1)), self.max_delay_seconds)


class ReliablePublisher:
    """Retry failed publisher calls with bounded exponential backoff."""

    def __init__(
        self, publisher: Publisher, policy: RetryPolicy | None = None, sleeper=time.sleep
    ) -> None:
        self.publisher = publisher
        self.policy = policy or RetryPolicy()
        self.sleeper = sleeper
        self.attempts = 0

    def publish(self, article: Article) -> PublishResult:
        self.attempts = 0
        last: PublishResult | None = None
        max_attempts = max(1, self.policy.max_attempts)
        for attempt in range(1, max_attempts + 1):
            self.attempts = attempt
            try:
                result = self.publisher.publish(article)
            except Exception as exc:
                result = PublishResult(
                    False, self.publisher.name, external_id=article.id, error=str(exc)
                )
            last = result
            if result.success:
                return result
            if attempt < max_attempts:
                self.sleeper(self.policy.delay(attempt))
        return last or PublishResult(
            False, self.publisher.name, external_id=article.id, error="publish failed"
        )
