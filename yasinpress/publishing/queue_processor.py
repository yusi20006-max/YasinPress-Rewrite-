from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from yasinpress.database.models import PublicationJob
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing import PublishResult
from yasinpress.publishing.history import DeliveryRecord


class PublicationQueueProcessor:
    """Core persistent queue engine and fair-scheduling / rate-limiting layer."""

    def __init__(self, repositories: SQLiteRepositories, publishers, max_global_per_hour: int = 10, max_source_per_hour: int = 5, lease_duration_seconds: int = 60, base_backoff_seconds: float = 2.0) -> None:
        self.repositories = repositories
        self.publishers = {p.name: p for p in publishers}
        self.max_global_per_hour = max_global_per_hour
        self.max_source_per_hour = max_source_per_hour
        self.lease_duration_seconds = lease_duration_seconds
        self.base_backoff_seconds = base_backoff_seconds

    def recover_expired_leases(self, now: datetime) -> int:
        stale_jobs = self.repositories.publication_queue.get_stale_leased_jobs(now)
        recovered_count = 0
        for job in stale_jobs:
            job.status = "retrying" if job.attempts > 0 else "pending"
            job.lease_expires_at = None
            job.last_error = "Lease expired (worker crash recovery)"
            self.repositories.publication_queue.save_job(job)
            recovered_count += 1
        return recovered_count

    def process_cycle(self, now: datetime | None = None) -> list[PublishResult]:
        if now is None:
            now = datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        self.recover_expired_leases(now)
        eligible = self.repositories.publication_queue.get_eligible_jobs(now)
        if not eligible:
            return []

        cutoff = now - timedelta(hours=1)
        recent_successes = [
            r for r in self.repositories.delivery_history.all()
            if r.success and r.created_at >= cutoff
        ]
        # Rate limits are publication-message limits, not unique-article limits.
        # A single article sent to two destinations consumes two publication slots.
        published_keys = {(r.article_id, r.destination) for r in recent_successes}
        available_slots = max(0, self.max_global_per_hour - len(recent_successes))
        if available_slots <= 0:
            return []

        source_counts: dict[str, int] = defaultdict(int)
        for record in recent_successes:
            article = self.repositories.articles.get(record.article_id)
            if article:
                source_counts[article.source] += 1

        by_priority: dict[int, dict[str, list[PublicationJob]]] = {}
        for job in eligible:
            by_priority.setdefault(job.priority, {}).setdefault(job.source, []).append(job)
        for sources in by_priority.values():
            for jobs in sources.values():
                jobs.sort(key=lambda j: j.created_at)

        selected_jobs: list[PublicationJob] = []
        selected_source_counts: dict[str, int] = defaultdict(int)
        for priority in sorted(by_priority, reverse=True):
            if available_slots <= 0:
                break
            sources = by_priority[priority]
            active_sources = list(sources)
            while active_sources and available_slots > 0:
                progressed = False
                for source in list(active_sources):
                    if source_counts[source] + selected_source_counts[source] >= self.max_source_per_hour or not sources[source]:
                        active_sources.remove(source)
                        continue
                    job = sources[source].pop(0)
                    key = (job.article_id, job.destination)
                    if key in published_keys:
                        continue
                    selected_jobs.append(job)
                    selected_source_counts[source] += 1
                    available_slots -= 1
                    progressed = True
                    if available_slots <= 0:
                        break
                if not progressed:
                    break

        results: list[PublishResult] = []
        for job in selected_jobs:
            job.status = "processing"
            job.lease_expires_at = now + timedelta(seconds=self.lease_duration_seconds)
            job.attempts += 1
            self.repositories.publication_queue.save_job(job)
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
            self.repositories.delivery_history.add(DeliveryRecord(article_id=article.id, destination=publisher.name, success=result.success, attempts=job.attempts, external_id=result.external_id, error=result.error, created_at=now))
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
