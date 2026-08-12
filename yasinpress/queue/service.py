from __future__ import annotations

from yasinpress.database.models import PublicationJob
from yasinpress.processing.pipeline import ProcessedArticle
from yasinpress.queue.engine import PublicationQueue


_PRIORITY_LEVELS = (
    ("breaking", 100),
    ("urgent", 80),
    ("important", 50),
    ("normal", 10),
)


def priority_level(value: int, breaking: bool = False) -> str:
    if breaking:
        return "breaking"
    for name, minimum in _PRIORITY_LEVELS[1:]:
        if value >= minimum:
            return name
    return "normal"


def enqueue_processed_article(
    queue: PublicationQueue,
    processed: ProcessedArticle,
    *,
    destination: str = "eitaa",
) -> PublicationJob:
    """Turn an accepted processed article into durable publication work."""
    article = processed.article
    level = priority_level(processed.priority.score, processed.breaking.is_breaking)
    job = PublicationJob(
        id=f"{article.id}:{destination}",
        article_id=article.id,
        destination=destination,
        status="pending",
        priority=100 if level == "breaking" else processed.priority.score,
        priority_level=level,
        source=article.source,
    )
    queue.enqueue(job)
    return job
