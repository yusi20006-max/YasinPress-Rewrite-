"""RSS feed parsing."""
from dataclasses import dataclass
from datetime import datetime, UTC
import xml.etree.ElementTree as ET

@dataclass(frozen=True)
class FeedItem:
    """An item parsed from an RSS feed."""
    title: str
    url: str
    content: str
    published_at: datetime


def parse_rss(xml_text: str) -> list[FeedItem]:
    """Parse RSS XML using the standard library."""
    root = ET.fromstring(xml_text)
    items: list[FeedItem] = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        url = item.findtext("link", "").strip()
        content = item.findtext("description", "").strip()
        if title and url:
            items.append(FeedItem(title, url, content, datetime.now(UTC)))
    return items
