from __future__ import annotations

from hashlib import sha256
from typing import Iterable

from yasinpress.sources.feed import FeedItem


def content_key(item: FeedItem) -> str:
    """Stable identity for an incoming feed item."""
    if item.url:
        return item.url.strip()
    raw = f"{item.title.strip()}\n{item.content.strip()}"
    return "sha256:" + sha256(raw.encode("utf-8")).hexdigest()


def unique_items(items: Iterable[FeedItem]) -> tuple[FeedItem, ...]:
    seen: set[str] = set()
    result: list[FeedItem] = []
    for item in items:
        key = content_key(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return tuple(result)
