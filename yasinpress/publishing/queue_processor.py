from __future__ import annotations

from datetime import UTC, datetime

from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing import PublishResult
from yasinpress.publishing.queue import QueueConfig, SQLitePublicationQueueEngine


class PublicationQueueProcessor:
    """Compatibility facade over the durable, version-aware publication queue engine."""

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
        self.publishers = tuple(publishers)
        self._engine = SQLitePublicationQueueEngine(
            repositories.connection,
            QueueConfig(
                global_limit=max_global_per_hour,
                source_limit=max_source_per_hour,
                lease=__import__("datetime").timedelta(seconds=lease_duration_seconds),
                retry_base=__import__("datetime").timedelta(seconds=base_backoff_seconds),
            ),
        )

    def recover_expired_leases(self, now: datetime) -> int:
        """Recover leased jobs whose workers stopped before completion."""
        return self._engine.recover_expired_leases(now)

    def process_cycle(self, now: datetime | None = None) -> list[PublishResult]:
        """Publish queued jobs using timestamp-aware idempotency and persistence."""
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)

        results: list[PublishResult] = []
        publisher_map = {publisher.name: publisher for publisher in self.publishers}
        max_jobs = max(1, self._engine.config.global_limit * max(1, len(publisher_map)))

        for _ in range(max_jobs):
            result = self._engine.run_once(publisher_map, self.repositories.articles, now=current)
            if result is None:
                break
            results.append(result)

        return results
