from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from yasinpress.database.models import PublicationJob
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing import PublishResult
from yasinpress.publishing.history import DeliveryRecord


class PublicationQueueProcessor:
    """Persistent queue engine with unique-article rate limiting and fair scheduling."""

    def __init__(
        self,
        repositories: SQLiteRepositories,
        publishers,
        max_global_per_hour: int = 10,
        max_source_per_hour: int = 5,
        lease_duration_seconds: int = 60,
        base_backoff_seconds: float = 2.0,
    ) -> None:
        self.repositories = repositories
        self.publishers = {p.name: p for p in publishers}
        self.max_global_per_hour = max_global_per_hour
        self.max_source_per_hour = max_source_per_hour
        self.lease_duration_seconds = lease_duration_seconds
        self.base_backoff_seconds = base_backoff_seconds

    def recover_expired_leases(self, now: datetime) -> int:
        if not hasattr(self.repositories, "publication_queue") or self.repositories.publication_queue is None:
            return 0
        if not hasattr(self.repositories, "connection") or self.repositories.connection is None:
            stale_jobs = self.repositories.publication_queue.get_stale_leased_jobs(now)
            recovered_count = 0
            for job in stale_jobs:
                job.status = "retrying" if job.attempts > 0 else "pending"
                job.lease_expires_at = None
                job.last_error = "Lease expired (worker crash recovery)"
                self.repositories.publication_queue.save_job(job)
                recovered_count += 1
            return recovered_count

        conn = self.repositories.connection
        recovered_count = 0
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            stale_jobs = self.repositories.publication_queue.get_stale_leased_jobs(now)
            for job in stale_jobs:
                job.status = "retrying" if job.attempts > 0 else "pending"
                job.lease_expires_at = None
                job.last_error = "Lease expired (worker crash recovery)"
                conn.execute(
                    """INSERT INTO publication_queue(id,article_id,destination,status,priority,priority_level,source,attempts,max_attempts,last_error,lease_expires_at,next_attempt_at,created_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,attempts=excluded.attempts,last_error=excluded.last_error,lease_expires_at=excluded.lease_expires_at,next_attempt_at=excluded.next_attempt_at""",
                    (job.id, job.article_id, job.destination, job.status, job.priority, job.priority_level, job.source, job.attempts, job.max_attempts, job.last_error,
                     job.lease_expires_at.isoformat() if job.lease_expires_at else None, job.next_attempt_at.isoformat() if job.next_attempt_at else None, job.created_at.isoformat()),
                )
                recovered_count += 1
        return recovered_count

    def _recent_delivery_state(self, now: datetime):
        cutoff = now - timedelta(hours=1)
        recent_successes = [
            record
            for record in self.repositories.delivery_history.all()
            if record.success and record.created_at >= cutoff
        ]
        published_keys = {(record.article_id, record.destination) for record in recent_successes}
        published_article_ids = {record.article_id for record in recent_successes}

        source_counts: dict[str, int] = defaultdict(int)
        counted_articles: set[str] = set()
        for record in recent_successes:
            if record.article_id in counted_articles:
                continue
            article = self.repositories.articles.get(record.article_id)
            if article:
                source_counts[article.source] += 1
                counted_articles.add(record.article_id)

        processing_jobs = [
            job
            for job in self.repositories.publication_queue.get_all_jobs()
            if job.status == "processing" and (job.lease_expires_at is None or job.lease_expires_at >= now)
        ]
        for job in processing_jobs:
            published_article_ids.add(job.article_id)
            if job.article_id not in counted_articles:
                source_counts[job.source] += 1
                counted_articles.add(job.article_id)

        return recent_successes, published_keys, published_article_ids, source_counts

    def _select_new_articles(
        self,
        eligible: tuple[PublicationJob, ...],
        published_article_ids: set[str],
        source_counts: dict[str, int],
        available_slots: int,
    ) -> set[str]:
        """Select new unique articles, preserving priority and source fairness."""
        if available_slots <= 0:
            return set()

        article_jobs: dict[str, list[PublicationJob]] = defaultdict(list)
        article_priority: dict[str, int] = {}
        article_source: dict[str, str] = {}
        for job in eligible:
            if job.article_id in published_article_ids:
                continue
            article_jobs[job.article_id].append(job)
            article_priority[job.article_id] = max(article_priority.get(job.article_id, job.priority), job.priority)
            article_source[job.article_id] = job.source

        by_priority: dict[int, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        for article_id, jobs in article_jobs.items():
            if not jobs:
                continue
            source = article_source[article_id]
            priority = article_priority[article_id]
            by_priority[priority][source].append(article_id)

        for sources in by_priority.values():
            for article_ids in sources.values():
                article_ids.sort(key=lambda article_id: min(job.created_at for job in article_jobs[article_id]))

        selected: set[str] = set()
        selected_source_counts: dict[str, int] = defaultdict(int)

        for priority in sorted(by_priority, reverse=True):
            if len(selected) >= available_slots:
                break
            sources = by_priority[priority]
            active_sources = list(sources)
            while active_sources and len(selected) < available_slots:
                progressed = False
                for source in list(active_sources):
                    if source_counts[source] + selected_source_counts[source] >= self.max_source_per_hour or not sources[source]:
                        active_sources.remove(source)
                        continue
                    article_id = sources[source].pop(0)
                    selected.add(article_id)
                    selected_source_counts[source] += 1
                    progressed = True
                    if len(selected) >= available_slots:
                        break
                if not progressed:
                    break

        return selected

    def process_cycle(self, now: datetime | None = None) -> list[PublishResult]:
        if now is None:
            now = datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        self.recover_expired_leases(now)
        if not hasattr(self.repositories, "publication_queue") or self.repositories.publication_queue is None:
            return []

        conn = self.repositories.connection
        selected_jobs: list[PublicationJob] = []

        with conn:
            conn.execute("BEGIN IMMEDIATE")
            eligible = self.repositories.publication_queue.get_eligible_jobs(now)
            if not eligible:
                return []

            _recent_successes, published_keys, published_article_ids, source_counts = self._recent_delivery_state(now)
            available_unique_slots = max(0, self.max_global_per_hour - len(published_article_ids))
            new_article_ids = self._select_new_articles(eligible, published_article_ids, source_counts, available_unique_slots)

            selected_article_ids = published_article_ids | new_article_ids
            selected_jobs = [
                job
                for job in eligible
                if job.article_id in selected_article_ids and (job.article_id, job.destination) not in published_keys
            ]
            selected_jobs.sort(key=lambda job: (-job.priority, job.created_at, job.source, job.destination))

            for job in selected_jobs:
                job.status = "processing"
                job.lease_expires_at = now + timedelta(seconds=self.lease_duration_seconds)
                job.attempts += 1
                conn.execute(
                    """INSERT INTO publication_queue(id,article_id,destination,status,priority,priority_level,source,attempts,max_attempts,last_error,lease_expires_at,next_attempt_at,created_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,attempts=excluded.attempts,last_error=excluded.last_error,lease_expires_at=excluded.lease_expires_at,next_attempt_at=excluded.next_attempt_at""",
                    (job.id, job.article_id, job.destination, job.status, job.priority, job.priority_level, job.source, job.attempts, job.max_attempts, job.last_error,
                     job.lease_expires_at.isoformat() if job.lease_expires_at else None, job.next_attempt_at.isoformat() if job.next_attempt_at else None, job.created_at.isoformat()),
                )

        results: list[PublishResult] = []
        for job in selected_jobs:
            article = self.repositories.articles.get(job.article_id)
            if not article:
                job.status = "dead_letter"
                job.lease_expires_at = None
                job.last_error = "Article not found"
                self.repositories.publication_queue.save_job(job)
                continue

            publisher = self.publishers.get(job.destination)
            if not publisher:
                job.status = "dead_letter"
                job.lease_expires_at = None
                job.last_error = f"Publisher {job.destination} not found"
                self.repositories.publication_queue.save_job(job)
                continue

            key = f"{article.id}:{publisher.name}"
            try:
                result = PublishResult(True, publisher.name, external_id=article.id) if self.repositories.idempotency.seen(key) else publisher.publish(article)
            except Exception as exc:
                result = PublishResult(False, publisher.name, error=str(exc))

            self.repositories.delivery_history.add(
                DeliveryRecord(
                    article_id=article.id,
                    destination=publisher.name,
                    success=result.success,
                    attempts=job.attempts,
                    external_id=result.external_id,
                    error=result.error,
                    created_at=now,
                )
            )

            if result.success:
                self.repositories.idempotency.mark(key)
                job.status = "succeeded"
                job.lease_expires_at = None
                job.last_error = None
            else:
                job.last_error = result.error or "Unknown publish error"
                if job.attempts >= job.max_attempts:
                    job.status = "dead_letter"
                    job.lease_expires_at = None
                else:
                    job.status = "retrying"
                    job.next_attempt_at = now + timedelta(seconds=self.base_backoff_seconds * (2 ** (job.attempts - 1)))
                    job.lease_expires_at = None

            self.repositories.publication_queue.save_job(job)
            results.append(result)

        return results
