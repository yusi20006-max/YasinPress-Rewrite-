from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from yasinpress.database.models import PublicationJob
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing import PublishResult
from yasinpress.publishing.history import DeliveryRecord


@dataclass(frozen=True)
class QueueConfig:
    global_limit: int = 30
    source_limit: int = 5
    lease: timedelta = timedelta(seconds=60)
    retry_base: timedelta = timedelta(seconds=2)
    max_attempts: int = 3


class SQLitePublicationQueueEngine:
    """Durable publication queue engine matching required persistence and API contracts."""

    def __init__(self, connection: sqlite3.Connection, config: QueueConfig | None = None) -> None:
        self.connection = connection
        self.config = config or QueueConfig()

        self.repositories = SQLiteRepositories.__new__(SQLiteRepositories)
        self.repositories.connection = connection
        from yasinpress.database.delivery import SQLiteDeliveryRepository
        from yasinpress.database.jobs import SQLiteJobRepository
        from yasinpress.database.sqlite import (
            SQLiteArticleRepository,
            SQLiteDeliveryHistory,
            SQLiteIdempotencyStore,
            SQLitePublicationQueue,
        )
        self.repositories.articles = SQLiteArticleRepository(connection=connection)
        self.repositories.jobs = SQLiteJobRepository(connection)
        self.repositories.deliveries = SQLiteDeliveryRepository(connection)
        self.repositories.delivery_history = SQLiteDeliveryHistory(connection)
        self.repositories.idempotency = SQLiteIdempotencyStore(connection)
        self.repositories.publication_queue = SQLitePublicationQueue(connection)

    def enqueue(self, job: PublicationJob) -> None:
        self.repositories.publication_queue.add_job(job)

    def get(self, job_id: str) -> PublicationJob | None:
        return self.repositories.publication_queue.get_job(job_id)

    def claim_next(self, now: datetime) -> PublicationJob | None:
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        conn = self.repositories.connection
        selected_job: PublicationJob | None = None

        with conn:
            conn.execute("BEGIN IMMEDIATE")

            eligible = self.repositories.publication_queue.get_eligible_jobs(now)
            if not eligible:
                return None

            cutoff = now - timedelta(hours=1)
            recent_successes = [
                r for r in self.repositories.delivery_history.all()
                if r.success and r.created_at >= cutoff
            ]

            processing_jobs = [
                j for j in self.repositories.publication_queue.get_all_jobs()
                if j.status == "processing" and (j.lease_expires_at is None or j.lease_expires_at >= now)
            ]

            consumed_slots = len(recent_successes) + len(processing_jobs)
            available_slots = max(0, self.config.global_limit - consumed_slots)
            if available_slots <= 0:
                return None

            source_counts: dict[str, int] = defaultdict(int)
            for record in recent_successes:
                article = self.repositories.articles.get(record.article_id)
                if article:
                    source_counts[article.source] += 1
                else:
                    job = self.repositories.publication_queue.get_job(f"{record.article_id}:{record.destination}")
                    if job:
                        source_counts[job.source] += 1

            for job in processing_jobs:
                source_counts[job.source] += 1

            by_priority: dict[int, dict[str, list[PublicationJob]]] = {}
            for job in eligible:
                by_priority.setdefault(job.priority, {}).setdefault(job.source, []).append(job)

            for sources in by_priority.values():
                for jobs in sources.values():
                    jobs.sort(key=lambda j: j.created_at)

            published_keys = {(r.article_id, r.destination) for r in recent_successes}

            for priority in sorted(by_priority, reverse=True):
                sources = by_priority[priority]
                active_sources = list(sources)
                while active_sources:
                    for source in list(active_sources):
                        if source_counts[source] >= self.config.source_limit or not sources[source]:
                            active_sources.remove(source)
                            continue
                        job = sources[source].pop(0)
                        key = (job.article_id, job.destination)
                        if key in published_keys:
                            continue
                        selected_job = job
                        break
                    if selected_job is not None:
                        break
                    break
                if selected_job is not None:
                    break

            if selected_job is None:
                return None

            selected_job.status = "processing"
            selected_job.lease_expires_at = now + self.config.lease
            selected_job.attempts += 1

            # Save the selected job within the transaction using direct SQL to avoid auto-commit
            conn.execute(
                """INSERT INTO publication_queue(id,article_id,destination,status,priority,priority_level,source,attempts,max_attempts,last_error,lease_expires_at,next_attempt_at,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,attempts=excluded.attempts,last_error=excluded.last_error,lease_expires_at=excluded.lease_expires_at,next_attempt_at=excluded.next_attempt_at""",
                (selected_job.id, selected_job.article_id, selected_job.destination, selected_job.status, selected_job.priority, selected_job.priority_level, selected_job.source, selected_job.attempts, selected_job.max_attempts, selected_job.last_error,
                 selected_job.lease_expires_at.isoformat() if selected_job.lease_expires_at else None, selected_job.next_attempt_at.isoformat() if selected_job.next_attempt_at else None, selected_job.created_at.isoformat()),
            )

        return selected_job

    def mark_success(self, job_id: str, now: datetime | None = None) -> None:
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        job = self.repositories.publication_queue.get_job(job_id)
        if not job:
            return
        job.status = "succeeded"
        job.lease_expires_at = None
        job.last_error = None
        self.repositories.publication_queue.save_job(job)

        key = f"{job.article_id}:{job.destination}"
        self.repositories.idempotency.mark(key)

        self.repositories.delivery_history.add(DeliveryRecord(
            article_id=job.article_id,
            destination=job.destination,
            success=True,
            attempts=job.attempts,
            external_id=job.article_id,
            error=None,
            created_at=current,
        ))

    def mark_failure(self, job_id: str, error: str, now: datetime | None = None) -> PublicationJob:
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        job = self.repositories.publication_queue.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        job.last_error = error
        if job.attempts >= self.config.max_attempts:
            job.status = "dead_letter"
            job.lease_expires_at = None
        else:
            job.status = "retrying"
            backoff = self.config.retry_base.total_seconds() * (2 ** (job.attempts - 1))
            job.next_attempt_at = current + timedelta(seconds=backoff)
            job.lease_expires_at = None
        self.repositories.publication_queue.save_job(job)

        self.repositories.delivery_history.add(DeliveryRecord(
            article_id=job.article_id,
            destination=job.destination,
            success=False,
            attempts=job.attempts,
            external_id=None,
            error=error,
            created_at=current,
        ))
        return job

    def recover_expired_leases(self, now: datetime) -> int:
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
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

    def metrics(self, now: datetime | None = None) -> dict[str, int]:
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        m = self.repositories.publication_queue.get_metrics()

        cutoff = current - timedelta(hours=1)
        recent_successes = [
            r for r in self.repositories.delivery_history.all()
            if r.success and r.created_at >= cutoff
        ]
        m["published_last_hour"] = len(recent_successes)
        m["remaining_global_capacity"] = max(0, self.config.global_limit - len(recent_successes))
        return m

    def run_once(
        self, publishers: dict[str, Any], store: Any, now: datetime | None = None
    ) -> PublishResult | None:
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)

        job = self.claim_next(current)
        if not job:
            return None

        article = store.get(job.article_id)
        if not article:
            job.status = "dead_letter"
            job.lease_expires_at = None
            job.last_error = "Article not found"
            self.repositories.publication_queue.save_job(job)
            return PublishResult(False, job.destination, error="Article not found")

        publisher = publishers.get(job.destination)
        if not publisher:
            job.status = "dead_letter"
            job.lease_expires_at = None
            job.last_error = f"Publisher {job.destination} not found"
            self.repositories.publication_queue.save_job(job)
            return PublishResult(False, job.destination, error="Publisher not found")

        key = f"{article.id}:{publisher.name}"
        try:
            if self.repositories.idempotency.seen(key):
                result = PublishResult(True, publisher.name, external_id=article.id)
            else:
                result = publisher.publish(article)
        except Exception as exc:
            result = PublishResult(False, publisher.name, error=str(exc))

        if result.success:
            self.mark_success(job.id, now=current)
            from dataclasses import replace
            updated_article = replace(article, published_to_channel_at=current)
            if hasattr(store, "save"):
                store.save(updated_article)
        else:
            self.mark_failure(job.id, result.error or "Unknown publish error", now=current)

        return result
