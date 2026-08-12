from __future__ import annotations

from yasinpress.database.models import PublicationJob
from yasinpress.processing.pipeline import ProcessedArticle
from yasinpress.queue.engine import PublicationQueue


_PRIORITY_VALUES = {
    "breaking": 100,
    "urgent": 80,
    "important": 50,
    "normal": 10,
}


def priority_level(score: int, processing_level: str, breaking: bool = False) -> str:
    if breaking:
        return "breaking"
    if processing_level == "high":
        return "urgent"
    if processing_level == "medium":
        return "important"
    return "normal"


def enqueue_processed_article(
    queue: PublicationQueue,
    processed: ProcessedArticle,
    *,
    destination: str = "eitaa",
) -> PublicationJob:
    """Turn an accepted processed article into durable publication work."""
    article = processed.article
    level = priority_level(
        processed.priority.score,
        processed.priority.level,
        processed.breaking.is_breaking,
    )
    job = PublicationJob(
        id=f"{article.id}:{destination}",
        article_id=article.id,
        destination=destination,
        status="pending",
        priority=_PRIORITY_VALUES[level],
        priority_level=level,
        source=article.source,
    )
    queue.enqueue(job)
    return job
