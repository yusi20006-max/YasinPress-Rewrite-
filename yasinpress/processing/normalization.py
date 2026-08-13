"""Article normalization."""

import json
from datetime import UTC, datetime

from yasinpress.core.helpers import stable_hash
from yasinpress.database.models import Article
from yasinpress.processing.headline import normalize_headline
from yasinpress.sources.feed import FeedItem


def normalize(item: FeedItem, source: str, event_id: str | None = None) -> Article:
    """Convert a feed item into an article model with a formatted News ID."""
    pub = item.published_at
    if pub is None:
        pub = datetime.now(UTC)
    elif pub.tzinfo is None:
        pub = pub.replace(tzinfo=UTC)

    yymmdd = pub.strftime("%y%m%d")
    h = stable_hash(item.url)[:6].upper()
    news_id = f"YP-{yymmdd}-{h}"

    metadata_dict = {}
    if getattr(item, "media_url", None):
        metadata_dict["media_url"] = item.media_url
    if getattr(item, "media_type", None):
        metadata_dict["media_type"] = item.media_type

    source_metadata = json.dumps(metadata_dict) if metadata_dict else None

    return Article(
        id=news_id,
        title=normalize_headline(item.title),
        url=item.url,
        content=item.content.strip(),
        source=source,
        published_at=pub,
        event_id=event_id,
        received_at=datetime.now(UTC),
        source_metadata=source_metadata,
    )
