"""RSS feed parsing."""

import email.utils
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class FeedItem:
    """An item parsed from an RSS feed."""

    title: str
    url: str
    content: str
    published_at: datetime
    source: str = ""


def _published_at(item: ET.Element) -> datetime:
    """Return the RSS publication time, falling back to fetch time."""
    raw = (item.findtext("pubDate") or item.findtext("published") or "").strip()
    if raw:
        try:
            parsed = email.utils.parsedate_to_datetime(raw)
            return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except (TypeError, ValueError, IndexError):
            pass
    return datetime.now(UTC)


def parse_rss(xml_text: str) -> list[FeedItem]:
    """Parse RSS XML using the standard library."""
    root = ET.fromstring(xml_text)
    items: list[FeedItem] = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        url = item.findtext("link", "").strip()
        content = item.findtext("description", "").strip()
        if title and url:
            items.append(FeedItem(title, url, content, _published_at(item)))
    return items
