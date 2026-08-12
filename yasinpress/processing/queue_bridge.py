from __future__ import annotations

from yasinpress.processing.pipeline import ProcessedArticle
from yasinpress.publishing.queue import SQLitePublicationQueueEngine


def enqueue_processed(
    queue: SQLitePublicationQueueEngine,
    processed: ProcessedArticle,
    destination: str,
) -> str:
    """Persist a processed article for publication without publishing inline."""
    job = queue.enqueue_article(
        processed.article,
        destination,
        priority=processed.priority.score,
        priority_level=processed.priority.level,
    )
    return job.id
