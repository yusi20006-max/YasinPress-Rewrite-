from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, replace
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
    """Application service joining processing, freshness filtering, publishing, and idempotency."""

    def __init__(
        self,
        *,
        source: str,
        ai: AIProvider | None = None,
        publishers: Iterable[Publisher] = (),
        repository=None,
        history=None,
        idempotency=None,
        retry_policy: RetryPolicy | None = None,
        max_article_age_hours: float = 12.0,
        breaking_max_article_age_hours: float = 24.0,
        allow_breaking_exemption: bool = True,
        max_publications_per_hour: int = 10,
        publication_queue=None,
    ) -> None:
        self.ai = ai
        self.pipeline = ArticlePipeline(source, repository=repository)
        self.publication_queue = publication_queue
        self.repository = repository
        self.publisher = PublishingOrchestrator(
            tuple(publishers),
            retry_policy=retry_policy,
            history=history,
            idempotency=idempotency,
        )
        self.history = history
        self.max_age = timedelta(hours=max_article_age_hours)
        # Keep legacy constructor arguments for compatibility. Freshness is
        # intentionally strict for every article, including breaking news.
        self.breaking_max_age = self.max_age
        self.allow_breaking_exemption = False
        self.max_publications_per_hour = max_publications_per_hour

    def _enrich(self, article: Article) -> Article:
        """Enrich only articles that already passed freshness filtering."""
        if self.ai is None:
            return article
        if hasattr(self.ai, "enrich"):
            result = self.ai.enrich(article)
            if getattr(result, "success", False):
                ai_state = "rewritten"
                if result.title == article.title and result.content == article.content:
                    ai_state = "fallback"
                return replace(
                    article,
                    title=result.title,
                    content=result.content,
                    ai_state=ai_state,
                    ai_error=None,
                )
            return replace(
                article,
                ai_state="failed",
                ai_error=getattr(result, "error", "AI failed"),
            )
        rewrite = getattr(self.ai, "rewrite", None)
        if rewrite is not None:
            return replace(
                article,
                content=rewrite(article.content),
                ai_state="rewritten",
                ai_error=None,
            )
        return article

    @staticmethod
    def _fresh(article: Article, now: datetime, max_age: timedelta) -> bool:
        """Return whether an article has a valid news timestamp within the age window."""
        if article.lifecycle_state == "timestamp_unknown":
            return False
        timestamp = article.news_timestamp
        if timestamp is None:
            return False
        timestamp = timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp.astimezone(UTC)
        return timestamp >= now - max_age

    def _fully_delivered(self, article: Article) -> bool:
        """Return true only when every configured destination already has this article."""
        if article.published_to_channel_at is None:
            return False
        if article.news_timestamp is not None and article.news_timestamp > article.published_to_channel_at + timedelta(seconds=5):
            return False
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

        def get_sort_key(item: Article) -> datetime:
            timestamp = item.news_timestamp
            return timestamp or datetime.fromtimestamp(0, tz=UTC)

        for article in sorted(articles, key=get_sort_key, reverse=True):
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
        # Normalize/deduplicate first; do not spend AI resources until the
        # normalized article has passed the mandatory freshness gate.
        result = self.pipeline.process(unique_items(items))
        normalized_articles = result.articles
        now = datetime.now(UTC)
        fresh_articles: list[Article] = []
        old_count = 0

        for article in normalized_articles:
            if self._fresh(article, now, self.max_age):
                fresh_articles.append(article)
            else:
                old_count += 1

        # AI is deliberately downstream of freshness filtering. This prevents
        # stale or timestamp-unknown RSS entries from consuming AI/queue work.
        enriched_fresh = tuple(self._enrich(article) for article in fresh_articles)
        articles_by_id = {article.id: article for article in enriched_fresh}
        all_articles = tuple(
            articles_by_id.get(article.id, article) for article in normalized_articles
        )

        undelivered = tuple(article for article in enriched_fresh if not self._fully_delivered(article))
        duplicate_count = len(enriched_fresh) - len(undelivered)

        if self.publication_queue is not None:
            from yasinpress.processing.breaking import detect_breaking
            from yasinpress.processing.priority import calculate_priority

            max_attempts = 3
            if self.publisher.publishers:
                policy = getattr(self.publisher.publishers[0], "policy", None)
                max_attempts = getattr(policy, "max_attempts", 3) if policy else 3

            queued_jobs = 0
            for article in undelivered:
                breaking_result = detect_breaking(
                    article.title,
                    article.content,
                    published_at=article.published_at,
                )
                priority_result = calculate_priority(article.title, article.content)
                if breaking_result.is_breaking:
                    priority_level, priority = "breaking", 40
                elif priority_result.level == "high":
                    priority_level, priority = "urgent", 30
                elif priority_result.level == "medium":
                    priority_level, priority = "important", 20
                else:
                    priority_level, priority = "normal", 10

                for publisher in self.publisher.publishers:
                    job_id = f"{article.id}:{publisher.publisher.name}"
                    get_job = getattr(self.publication_queue, "get_job", None)
                    existing_job = get_job(job_id) if get_job is not None else None
                    needs_queue = existing_job is None or article.published_to_channel_at is None
                    if (
                        not needs_queue
                        and article.news_timestamp is not None
                        and article.news_timestamp > article.published_to_channel_at + timedelta(seconds=5)
                    ):
                        needs_queue = True

                    if needs_queue:
                        self.publication_queue.add_job(
                            PublicationJob(
                                id=job_id,
                                article_id=article.id,
                                destination=publisher.publisher.name,
                                status="pending",
                                priority=priority,
                                priority_level=priority_level,
                                source=article.source,
                                max_attempts=max_attempts,
                            )
                        )
                        queued_jobs += 1

            return ProcessingReport(
                PipelineResult(len(all_articles), result.rejected, all_articles),
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
        updated_articles: dict[str, Article] = {}

        for article in selected:
            report = self.publisher.publish(article)
            results.extend(report.results)
            if any(result.success for result in report.results):
                published = replace(article, published_to_channel_at=datetime.now(UTC))
                updated_articles[published.id] = published
                if self.repository is not None:
                    self.repository.save(published)

        final_articles = tuple(updated_articles.get(article.id, article) for article in all_articles)
        return ProcessingReport(
            PipelineResult(len(final_articles), result.rejected, final_articles),
            PublishReport(tuple(results)),
            old_count=old_count,
            queued_count=queued_count,
            duplicate_count=duplicate_count,
        )
