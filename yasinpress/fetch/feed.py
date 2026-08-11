from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlparse

from yasinpress.fetch.http import fetch_text
from yasinpress.sources.feed import FeedItem, parse_rss


@dataclass(frozen=True)
class FeedFetchResult:
    url: str
    source: str
    items: tuple[FeedItem, ...]


class FeedFetcher:
    def __init__(self, fetch: Callable[[str], str] = fetch_text, timeout: float = 20.0) -> None:
        self.fetch = fetch
        self.timeout = timeout

    def fetch_url(self, url: str) -> FeedFetchResult:
        payload = self.fetch(url, timeout=self.timeout)
        source = urlparse(url).hostname or url
        items = tuple(
            FeedItem(item.title, item.url, item.content, item.published_at, source)
            for item in parse_rss(payload)
        )
        return FeedFetchResult(url, source, items)

    def fetch_many(self, urls: tuple[str, ...]) -> tuple[FeedFetchResult, ...]:
        return tuple(self.fetch_url(url) for url in urls)
