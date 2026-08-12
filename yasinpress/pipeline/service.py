from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from yasinpress.ai.base import AIProvider
from yasinpress.database.models import PRIORITY_LEVELS, Article
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
    duplicate_count: int = 0
    dead_letter_count: int = 0


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
        max_publications_per_source_per_hour: int = 5,
        max_delivery_attempts: int = 5,
    ) -> None:
        self.ai = ai
        self.pipeline = ArticlePipeline(source)
        self.publisher = PublishingOrchestrator(
            tuple(publishers),
            retry_policy=retry_policy,
            history=history,
            idempotency=idempotency,
        )
        self.history = history
        self.max_age = timedelta(hours=max_article_age_hours)
        self.max_publications_per_hour = max_publications_per_hour
        self.max_publications_per_source_per_hour = max_publications_per_source_per_hour
        self.max_delivery_attempts = max_delivery_attempts

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
                    priority=article.priority,
                    is_ai_rewritten=True,
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
                priority=article.priority,
                is_ai_rewritten=True,
            )
        return article

    def _was_delivered(self, article: Article) -> bool:
        for publisher in self.publisher.publishers:
            key = f"{article.id}:{publisher.publisher.name}"
            if self.publisher.idempotency.seen(key):
                return True
        return False

    def _is_dead_letter(self, article: Article) -> bool:
        """An article is dead-lettered once it has failed at least
        max_delivery_attempts times across all processing cycles with no
        successful delivery ever recorded. Dead-lettered articles are
        permanently excluded from future selection."""
        if self.history is None or self.max_delivery_attempts <= 0:
            return False
        failures = 0
        for record in self.history.for_article(article.id):
            if record.success:
                return False
            failures += 1
        return failures >= self.max_delivery_attempts

    def _published_counts_last_hour(self, now: datetime) -> tuple[int, dict[str, int]]:
        cutoff = now - timedelta(hours=1)
        total = 0
        per_source: dict[str, int] = defaultdict(int)
        if self.history is not None:
            for record in self.history.all():
                if record.success and record.created_at >= cutoff:
                    total += 1
                    if record.source:
                        per_source[record.source] += 1
        return total, dict(per_source)

    def _select_fair_batch(
        self,
        articles: tuple[Article, ...],
        *,
        global_budget: int,
        per_source_remaining: dict[str, int],
    ) -> tuple[Article, ...]:
        """Select articles respecting the global hourly budget and a
        per-source hourly budget, processing higher-priority tiers first
        and using fair round-robin ordering by source within each tier."""
        selected: list[Article] = []
        remaining_global = global_budget
        remaining_by_source: dict[str, int] = defaultdict(
            lambda: self.max_publications_per_source_per_hour
        )
        remaining_by_source.update(per_source_remaining)

        for tier in PRIORITY_LEVELS:
            if remaining_global <= 0:
                break
            tier_articles = tuple(a for a in articles if a.priority == tier)
            if not tier_articles:
                continue

            buckets: dict[str, list[Article]] = defaultdict(list)
            for article in sorted(tier_articles, key=lambda item: item.published_at, reverse=True):
                buckets[article.source].append(article)

            progressed = True
            while remaining_global > 0 and buckets and progressed:
                progressed = False
                for source in tuple(buckets):
                    bucket = buckets[source]
                    if not bucket:
                        del buckets[source]
                        continue
                    if remaining_by_source[source] <= 0:
                        del buckets[source]
                        continue
                    selected.append(bucket.pop(0))
                    remaining_by_source[source] -= 1
                    remaining_global -= 1
                    progressed = True
                    if remaining_global <= 0:
                        break
        return tuple(selected)

    def process(self, items: Iterable[FeedItem]) -> ProcessingReport:
        result = self.pipeline.process(unique_items(items))
        articles = tuple(self._enrich(article) for article in result.articles)
        now = datetime.now(UTC)
        cutoff = now - self.max_age
        old_count = sum(article.published_at < cutoff for article in articles)
        candidates = tuple(article for article in articles if article.published_at >= cutoff)

        not_delivered = tuple(article for article in candidates if not self._was_delivered(article))
        duplicate_count = len(candidates) - len(not_delivered)

        dead_letters = tuple(a for a in not_delivered if self._is_dead_letter(a))
        undelivered = tuple(a for a in not_delivered if a not in dead_letters)
        dead_letter_count = len(dead_letters)

        published_last_hour, per_source_published = self._published_counts_last_hour(now)
        available = max(0, self.max_publications_per_hour - published_last_hour)
        per_source_remaining = {
            source: max(0, self.max_publications_per_source_per_hour - count)
            for source, count in per_source_published.items()
        }
        selected = self._select_fair_batch(
            undelivered, global_budget=available, per_source_remaining=per_source_remaining
        )
        queued_count = max(0, len(undelivered) - len(selected))

        results: list[PublishResult] = []
        for article in selected:
            report = self.publisher.publish(article)
            results.extend(report.results)

        return ProcessingReport(
            PipelineResult(len(articles), result.rejected, articles),
            PublishReport(tuple(results)),
            old_count=old_count,
            queued_count=queued_count,
            duplicate_count=duplicate_count,
            dead_letter_count=dead_letter_count,
        )
