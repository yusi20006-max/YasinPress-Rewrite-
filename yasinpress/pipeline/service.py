from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from yasinpress.ai.base import AIProvider
from yasinpress.database.models import Article
from yasinpress.pipeline.dedup import unique_items
from yasinpress.pipeline.runtime import ArticlePipeline, PipelineResult
from yasinpress.publishing import Publisher, PublishResult
from yasinpress.publishing.orchestrator import PublishingOrchestrator, PublishReport
from yasinpress.publishing.reliability import RetryPolicy
from yasinpress.sources.feed import FeedItem


@dataclass(frozen=True)
class ProcessingReport:
    pipeline: PipelineResult
    publications: PublishReport
    old_count: int = 0
    queued_count: int = 0


class ProcessingService:
    """Application service joining processing, freshness filtering, fair publishing, and idempotency."""

    def __init__(
        self,
        *,
        source: str,
        ai: AIProvider | None = None,
        publishers: Iterable[Publisher] = (),
        history=None,
        idempotency=None,
        retry_policy: RetryPolicy | None = None,
        max_article_age_hours: float = 6.0,
        max_publications_per_hour: int = 10,
    ) -> None:
        self.ai = ai
        self.pipeline = ArticlePipeline(source)
        self.publisher = PublishingOrchestrator(
            tuple(publishers),
            retry_policy=retry_policy,
            history=history,
            idempotency=idempotency,
        )
        self.max_age = timedelta(hours=max_article_age_hours)
        self.max_publications_per_hour = max_publications_per_hour
        self._published_timestamps: list[datetime] = []

    def _enrich(self, article: Article) -> Article:
        if self.ai is None:
            return article
        if hasattr(self.ai, "enrich"):
            result = self.ai.enrich(article)
            if getattr(result, "success", False):
                return Article(
                    id=article.id,
                    title=result.title,
                    url=article.url,
                    content=result.content,
                    source=article.source,
                    published_at=article.published_at,
                    category=article.category,
                )
            return article
        rewrite = getattr(self.ai, "rewrite", None)
        if rewrite is not None:
            content = rewrite(article.content)
            return Article(
                id=article.id,
                title=article.title,
                url=article.url,
                content=content,
                source=article.source,
                published_at=article.published_at,
                category=article.category,
            )
        return article

    def _select_fair_batch(self, articles: tuple[Article, ...], now: datetime) -> tuple[Article, ...]:
        cutoff = now - self.max_age
        recent = [article for article in articles if article.published_at >= cutoff]
        buckets: dict[str, list[Article]] = defaultdict(list)
        for article in sorted(recent, key=lambda item: item.published_at, reverse=True):
            buckets[article.source].append(article)

        selected: list[Article] = []
        while len(selected) < self.max_publications_per_hour and buckets:
            for source in tuple(buckets):
                bucket = buckets[source]
                if not bucket:
                    del buckets[source]
                    continue
                selected.append(bucket.pop(0))
                if len(selected) >= self.max_publications_per_hour:
                    break
        return tuple(selected)

    def process(self, items: Iterable[FeedItem]) -> ProcessingReport:
        result = self.pipeline.process(unique_items(items))
        articles = tuple(self._enrich(article) for article in result.articles)
        now = datetime.now(UTC)
        cutoff = now - self.max_age
        old_count = sum(article.published_at < cutoff for article in articles)
        candidates = tuple(article for article in articles if article.published_at >= cutoff)

        self._published_timestamps = [
            timestamp for timestamp in self._published_timestamps if now - timestamp < timedelta(hours=1)
        ]
        available = max(0, self.max_publications_per_hour - len(self._published_timestamps))
        selected = self._select_fair_batch(candidates, now)[:available]
        queued_count = max(0, len(candidates) - len(selected))

        results: list[PublishResult] = []
        for article in selected:
            report = self.publisher.publish(article)
            results.extend(report.results)
            if report.success_count:
                self._published_timestamps.append(datetime.now(UTC))

        return ProcessingReport(
            PipelineResult(len(articles), result.rejected, articles),
            PublishReport(tuple(results)),
            old_count=old_count,
            queued_count=queued_count,
        )
