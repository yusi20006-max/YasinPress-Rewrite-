from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.processing.cleaner import clean_html
from yasinpress.processing.normalization import normalize
from yasinpress.processing.validator import validate_article
from yasinpress.sources.feed import FeedItem


@dataclass(frozen=True)
class PipelineResult:
    processed: int
    rejected: int
    articles: tuple[Article, ...]


from typing import Any


class ArticlePipeline:
    """Deterministic feed-item processing boundary."""

    def __init__(self, source: str, *, duplicate: Callable[[Article], bool] | None = None, repository: Any = None) -> None:
        self.source = source
        self.duplicate = duplicate or (lambda _: False)
        self.repository = repository

    def process(self, items: Iterable[FeedItem]) -> PipelineResult:
        articles: list[Article] = []
        rejected = 0
        for item in items:
            normalized = FeedItem(
                title=item.title.strip(),
                url=item.url.strip(),
                content=clean_html(item.content),
                published_at=item.published_at,
                source=item.source,
                media_url=getattr(item, "media_url", None),
                media_type=getattr(item, "media_type", None),
                updated_at=getattr(item, "updated_at", None),
                fetched_at=getattr(item, "fetched_at", datetime.now(UTC)),
            )
            article = normalize(normalized, item.source or self.source, repository=self.repository)
            if self.duplicate(article):
                continue
            try:
                validate_article(article)
            except ValueError:
                rejected += 1
                continue
            from dataclasses import replace
            article = replace(article, processed_at=datetime.now(UTC))
            articles.append(article)
        return PipelineResult(len(articles), rejected, tuple(articles))
