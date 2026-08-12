from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import feedparser
import httpx


@dataclass(frozen=True)
class RSSFeed:
    name: str
    url: str


# Curated Persian news feeds. Availability is checked at startup instead of
# assuming that a publisher's RSS endpoint remains unchanged forever.
RSS_CATALOG: tuple[RSSFeed, ...] = (
    RSSFeed("BBC Persian", "https://feeds.bbci.co.uk/persian/rss.xml"),
    RSSFeed(
        "BBC Persian - Iran Features", "https://feeds.bbci.co.uk/persian/iran_features/rss.xml"
    ),
    RSSFeed("DW Persian", "https://rss.dw.com/xml/rss-fa-all"),
    RSSFeed("Euronews Persian", "https://per.euronews.com/rss"),
    RSSFeed("France 24 Persian", "https://www.france24.com/fa/rss"),
    RSSFeed("VOA Persian", "https://ir.voanews.com/rss"),
    RSSFeed("IRNA", "https://www.irna.ir/rss"),
    RSSFeed("ISNA", "https://www.isna.ir/rss"),
    RSSFeed("Mehr News", "https://www.mehrnews.com/rss"),
    RSSFeed("Tasnim", "https://www.tasnimnews.com/fa/rss"),
    RSSFeed("ILNA", "https://www.ilna.ir/rss"),
)


def probe_feed(feed: RSSFeed, timeout: float = 5.0) -> RSSFeed | None:
    """Return a feed only when its endpoint responds with parseable entries."""
    try:
        response = httpx.get(feed.url, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        if parsed.bozo and not parsed.entries:
            return None
        if not parsed.entries:
            return None
        return feed
    except (httpx.HTTPError, ValueError, OSError):
        return None


def active_feeds(timeout: float = 5.0) -> tuple[RSSFeed, ...]:
    """Return catalog feeds that currently respond with parseable entries."""
    active: list[RSSFeed] = []
    with ThreadPoolExecutor(max_workers=min(8, len(RSS_CATALOG))) as pool:
        futures = {pool.submit(probe_feed, feed, timeout): feed for feed in RSS_CATALOG}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                active.append(result)
    order = {feed.url: index for index, feed in enumerate(RSS_CATALOG)}
    return tuple(sorted(active, key=lambda feed: order[feed.url]))
