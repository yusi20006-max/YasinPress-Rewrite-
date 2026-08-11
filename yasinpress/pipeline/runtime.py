from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

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


class ArticlePipeline:
    """Deterministic feed-item processing boundary."""

    def __init__(self, source: str, *, duplicate: Callable[[Article], bool] | None = None) -> None:
        self.source = source
        self.duplicate = duplicate or (lambda _: False)

    def process(self, items: Iterable[FeedItem]) -> PipelineResult:
        articles: list[Article] = []
        rejected = 0
        for item in items:
            normalized = FeedItem(
                item.title.strip(), item.url.strip(), clean_html(item.content), item.published_at
            )
            article = normalize(normalized, self.source)
            if self.duplicate(article):
                continue
            try:
                validate_article(article)
            except ValueError:
                rejected += 1
                continue
            articles.append(article)
        return PipelineResult(len(articles), rejected, tuple(articles))
