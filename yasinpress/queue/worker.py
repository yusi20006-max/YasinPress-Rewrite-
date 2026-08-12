from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from yasinpress.database.models import Article, PublicationJob
from yasinpress.queue.engine import PublicationQueue


@dataclass(frozen=True)
class QueueWorkResult:
    job_id: str | None
    success: bool
    error: str | None = None


class PublicationWorker:
    """Execute durable publication jobs without coupling the queue to a destination."""

    def __init__(
        self,
        queue: PublicationQueue,
        article_loader: Callable[[str], Article | None],
        publisher: Callable[[Article, str], object],
    ) -> None:
        self.queue = queue
        self.article_loader = article_loader
        self.publisher = publisher

    def run_once(self, now: datetime | None = None) -> QueueWorkResult:
        now = now or datetime.now(UTC)
        job = self.queue.claim(now)
        if job is None:
            return QueueWorkResult(None, False, None)

        article = self.article_loader(job.article_id)
        if article is None:
            error = f"article not found: {job.article_id}"
            self.queue.fail(job.id, error, now)
            return QueueWorkResult(job.id, False, error)

        try:
            result = self.publisher(article, job.destination)
            success = bool(getattr(result, "success", result))
            if success:
                self.queue.succeed(job.id, now)
                return QueueWorkResult(job.id, True)
            error = str(getattr(result, "error", "publication failed"))
        except Exception as exc:  # destination failures must not kill the worker
            error = str(exc) or exc.__class__.__name__

        self.queue.fail(job.id, error, now)
        return QueueWorkResult(job.id, False, error)
