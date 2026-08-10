from __future__ import annotations

from dataclasses import dataclass

from yasinpress.database.models import Article
from yasinpress.publishing import PublishResult, Publisher


@dataclass(frozen=True)
class PublishReport:
    results: tuple[PublishResult, ...]

    @property
    def success_count(self) -> int:
        return sum(result.success for result in self.results)


class SafePublisher:
    """Isolate failures from individual publishing destinations."""

    def __init__(self, publisher: Publisher) -> None:
        self.publisher = publisher

    def publish(self, article: Article) -> PublishResult:
        try:
            return self.publisher.publish(article)
        except Exception as exc:
            return PublishResult(False, self.publisher.name, error=str(exc))


class PublishingOrchestrator:
    def __init__(self, publishers: list[Publisher] | tuple[Publisher, ...] = ()) -> None:
        self.publishers = tuple(SafePublisher(publisher) for publisher in publishers)

    def publish(self, article: Article) -> PublishReport:
        return PublishReport(tuple(publisher.publish(article) for publisher in self.publishers))
