from __future__ import annotations

from datetime import UTC, datetime, timedelta

from yasinpress.database.models import PublicationJob
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing import PublishResult
from yasinpress.publishing.history import DeliveryRecord


class PublicationQueueProcessor:
    """Core persistent queue engine and fair-scheduling / rate-limiting layer."""

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
        """Find and recover any jobs stuck in processing where the lease has expired."""
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
        """Execute one scheduling and publication cycle."""
        if now is None:
            now = datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        # 1. Recover expired leases
        self.recover_expired_leases(now)

        # 2. Get eligible pending or retrying jobs
        eligible = self.repositories.publication_queue.get_eligible_jobs(now)
        if not eligible:
            return []

        # 3. Compute rolling hourly global published count
        cutoff = now - timedelta(hours=1)
        history_records = self.repositories.delivery_history.all()
        recent_successes = [r for r in history_records if r.success and r.created_at >= cutoff]
        unique_articles_published = {r.article_id for r in recent_successes}
        global_published_count = len(unique_articles_published)

        if global_published_count >= self.max_global_per_hour:
            return []

        # 4. Compute rolling hourly per-source published count
        source_counts: dict[str, int] = {}
        for article_id in unique_articles_published:
            art = self.repositories.articles.get(article_id)
            if art:
                source_counts[art.source] = source_counts.get(art.source, 0) + 1

        # 5. Fair scheduling across sources grouped by priority DESC
        # Group eligible jobs by their priority score
        by_priority: dict[int, list[PublicationJob]] = {}
        for job in eligible:
            by_priority.setdefault(job.priority, []).append(job)

        selected_jobs: list[PublicationJob] = []
        available_slots = self.max_global_per_hour - global_published_count

        for priority in sorted(by_priority.keys(), reverse=True):
            if available_slots <= 0:
                break

            priority_jobs = by_priority[priority]

            # Group jobs in this priority level by source
            by_source: dict[str, list[PublicationJob]] = {}
            for job in priority_jobs:
                by_source.setdefault(job.source, []).append(job)

            # Sort jobs for each source by created_at (oldest first)
            for src in by_source:
                by_source[src].sort(key=lambda j: j.created_at)

            # Round-robin distribution of sources
            sources = list(by_source.keys())
            while sources and available_slots > 0:
                for src in list(sources):
                    if available_slots <= 0:
                        break

                    # Check if this source has hit its limit (5/hour)
                    if source_counts.get(src, 0) >= self.max_source_per_hour:
                        sources.remove(src)
                        continue

                    jobs_list = by_source[src]
                    if not jobs_list:
                        sources.remove(src)
                        continue

                    # Select the oldest job from this source
                    job_to_select = jobs_list.pop(0)
                    selected_jobs.append(job_to_select)

                    # Update local counts
                    source_counts[src] = source_counts.get(src, 0) + 1
                    if job_to_select.article_id not in unique_articles_published:
                        unique_articles_published.add(job_to_select.article_id)
                        available_slots -= 1

        # 6. Publish the selected jobs
        results: list[PublishResult] = []
        for job in selected_jobs:
            # Safe lock lease
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

            # Check destination idempotency key
            key = f"{article.id}:{publisher.name}"
            try:
                if self.repositories.idempotency.seen(key):
                    result = PublishResult(True, publisher.name, external_id=article.id)
                else:
                    # Publish!
                    result = publisher.publish(article)
            except Exception as exc:
                result = PublishResult(False, publisher.name, error=str(exc))

            # Record the delivery record in the persistent history
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
                # Mark as seen in idempotency store
                self.repositories.idempotency.mark(key)

                # Set job status to succeeded
                job.status = "succeeded"
                job.lease_expires_at = None
                job.last_error = None
                self.repositories.publication_queue.save_job(job)
                results.append(result)
            else:
                # Failed attempt
                job.last_error = result.error or "Unknown publish error"
                if job.attempts >= job.max_attempts:
                    job.status = "dead_letter"
                    job.lease_expires_at = None
                else:
                    job.status = "retrying"
                    # Exponential backoff
                    delay = self.base_backoff_seconds * (2 ** (job.attempts - 1))
                    job.next_attempt_at = now + timedelta(seconds=delay)
                    job.lease_expires_at = None
                self.repositories.publication_queue.save_job(job)
                results.append(result)

        return results
