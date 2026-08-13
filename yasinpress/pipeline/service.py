from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from yasinpress.ai.base import AIProvider
from yasinpress.database.models import Article, PublicationJob
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
        max_article_age_hours: float = 12.0,
        breaking_max_article_age_hours: float = 24.0,
        allow_breaking_exemption: bool = True,
        max_publications_per_hour: int = 30,
        publication_queue=None,
    ) -> None:
        self.ai = ai
        self.pipeline = ArticlePipeline(source)
        self.publication_queue = publication_queue
        self.publisher = PublishingOrchestrator(
            tuple(publishers),
            retry_policy=retry_policy,
            history=history,
            idempotency=idempotency,
        )
        self.history = history
        self.max_age = timedelta(hours=max_article_age_hours)
        # Breaking news follows the same 12-hour freshness contract. Keep the
        # legacy constructor arguments for compatibility, but do not allow
        # them to create a freshness exemption.
        self.breaking_max_age = self.max_age
        self.allow_breaking_exemption = False
        self.max_publications_per_hour = max_publications_per_hour

    def _enrich(self, article: Article) -> Article:
        if self.ai is None:
            return article
        if hasattr(self.ai, "enrich"):
            result = self.ai.enrich(article)
            if getattr(result, "success", False):
                ai_state = "rewritten"
                if result.title == article.title and result.content == article.content:
                    ai_state = "fallback"
                return Article(
                    id=article.id, title=result.title, url=article.url, content=result.content,
                    source=article.source, published_at=article.published_at, category=article.category,
                    event_id=article.event_id, received_at=article.received_at,
                    lifecycle_state=article.lifecycle_state, ai_state=ai_state, ai_error=None,
                    source_metadata=article.source_metadata,
                )
            return Article(
                id=article.id, title=article.title, url=article.url, content=article.content,
                source=article.source, published_at=article.published_at, category=article.category,
                event_id=article.event_id, received_at=article.received_at,
                lifecycle_state=article.lifecycle_state, ai_state="failed",
                ai_error=getattr(result, "error", "AI failed"), source_metadata=article.source_metadata,
            )
        rewrite = getattr(self.ai, "rewrite", None)
        if rewrite is not None:
            content = rewrite(article.content)
            return Article(
                id=article.id, title=article.title, url=article.url, content=content,
                source=article.source, published_at=article.published_at, category=article.category,
                event_id=article.event_id, received_at=article.received_at,
                lifecycle_state=article.lifecycle_state, ai_state="rewritten", ai_error=None,
                source_metadata=article.source_metadata,
            )
        return article

    def _fully_delivered(self, article: Article) -> bool:
        """Return true only when every configured destination already has this article."""
        return bool(self.publisher.publishers) and all(
            self.publisher.idempotency.seen(f"{article.id}:{publisher.publisher.name}")
            for publisher in self.publisher.publishers
        )

    def _published_last_hour(self, now: datetime) -> int:
        cutoff = now - timedelta(hours=1)
        if self.history is not None:
            return sum(record.success and record.created_at >= cutoff for record in self.history.all())
        return 0

    def _select_fair_batch(self, articles: tuple[Article, ...]) -> tuple[Article, ...]:
        buckets: dict[str, list[Article]] = defaultdict(list)
        for article in sorted(articles, key=lambda item: item.published_at, reverse=True):
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
        candidates = []
        old_count = 0
        from yasinpress.processing.breaking import detect_breaking

        for article in articles:
            detect_breaking(
                article.title,
                article.content,
                published_at=article.published_at,
            )
            cutoff = now - self.max_age
            pub = article.published_at
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=UTC)
            if pub < cutoff:
                old_count += 1
            else:
                candidates.append(article)

        candidates = tuple(candidates)
        undelivered = tuple(article for article in candidates if not self._fully_delivered(article))
        duplicate_count = len(candidates) - len(undelivered)

        if self.publication_queue is not None:
            from yasinpress.processing.priority import calculate_priority

            max_att = 3
            if self.publisher.publishers:
                policy = getattr(self.publisher.publishers[0], "policy", None)
                max_att = getattr(policy, "max_attempts", 3) if policy else 3

            queued_jobs = 0
            for article in undelivered:
                breaking_res = detect_breaking(
                    article.title,
                    article.content,
                    published_at=article.published_at,
                )
                priority_res = calculate_priority(article.title, article.content)
                if breaking_res.is_breaking:
                    level, score = "breaking", 40
                elif priority_res.level == "high":
                    level, score = "urgent", 30
                elif priority_res.level == "medium":
                    level, score = "important", 20
                else:
                    level, score = "normal", 10

                for publisher in self.publisher.publishers:
                    job_id = f"{article.id}:{publisher.publisher.name}"
                    if not self.publication_queue.exists(job_id):
                        self.publication_queue.add_job(
                            PublicationJob(
                                id=job_id,
                                article_id=article.id,
                                destination=publisher.publisher.name,
                                status="pending",
                                priority=score,
                                priority_level=level,
                                source=article.source,
                                max_attempts=max_att,
                            )
                        )
                        queued_jobs += 1

            return ProcessingReport(
                PipelineResult(len(articles), result.rejected, articles),
                PublishReport(()),
                old_count=old_count,
                queued_count=queued_jobs,
                duplicate_count=duplicate_count,
            )

        published_last_hour = self._published_last_hour(now)
        available = max(0, self.max_publications_per_hour - published_last_hour)
        selected = self._select_fair_batch(undelivered)[:available]
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
        )
