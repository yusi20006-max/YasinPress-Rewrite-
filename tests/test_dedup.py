from datetime import datetime, timezone

from yasinpress.pipeline.dedup import content_key, unique_items
from yasinpress.sources.feed import FeedItem


def item(title: str, url: str, content: str = "x") -> FeedItem:
    return FeedItem(title, url, content, datetime.now(timezone.utc))


def test_unique_items_deduplicates_by_url():
    a = item("one", "https://example.com/a")
    b = item("changed title", "https://example.com/a")
    assert unique_items([a, b]) == (a,)


def test_content_key_falls_back_to_content_hash():
    assert content_key(item("same", "", "body")).startswith("sha256:")
