"""Article normalization."""

import json
from datetime import UTC, datetime

from yasinpress.core.helpers import stable_hash
from yasinpress.database.models import Article
from yasinpress.processing.headline import normalize_headline
from yasinpress.sources.feed import FeedItem


from typing import Any

def normalize(item: FeedItem, source: str, event_id: str | None = None, repository: Any = None) -> Article:
    """Convert a feed item into an article model with a formatted News ID."""
    updated_val = getattr(item, "updated_at", None)
    published_val = getattr(item, "published_at", None)
    fetched_val = getattr(item, "fetched_at", None) or datetime.now(UTC)

    # Resolve deterministic news_timestamp
    news_ts = None
    for dt_val in [updated_val, published_val]:
        if dt_val is not None and dt_val != datetime.fromtimestamp(0, tz=UTC):
            news_ts = dt_val if dt_val.tzinfo else dt_val.replace(tzinfo=UTC)
            break

    # URL lookup to reuse existing ID and preserve properties
    existing_id = None
    existing_published_to_channel_at = None
    existing_published_at = None
    existing_updated_at = None
    if repository is not None:
        try:
            existing = repository.get(item.url)
            if existing is not None:
                existing_id = existing.id
                existing_published_to_channel_at = existing.published_to_channel_at
                existing_published_at = existing.published_at
                existing_updated_at = existing.updated_at
        except Exception:
            pass

    # Resolve existing news_timestamp
    existing_news_ts = None
    if existing_id:
        for dt_val in [existing_updated_at, existing_published_at]:
            if dt_val is not None and dt_val != datetime.fromtimestamp(0, tz=UTC):
                existing_news_ts = dt_val if dt_val.tzinfo else dt_val.replace(tzinfo=UTC)
                break

    # Determine if incoming news_ts is a newer update
    is_valid_update = False
    if news_ts is not None:
        if existing_id is not None and existing_news_ts is None:
            is_valid_update = True
        elif existing_news_ts is not None:
            from datetime import timedelta
            if news_ts > existing_news_ts + timedelta(seconds=5):
                is_valid_update = True

    # Determine status/lifecycle_state
    if news_ts is None:
        lifecycle_state = "timestamp_unknown"
        yymmdd = fetched_val.strftime("%y%m%d")
    else:
        lifecycle_state = "fetched"
        yymmdd = news_ts.strftime("%y%m%d")

    if existing_id:
        news_id = existing_id
        if (published_val is None or published_val == datetime.fromtimestamp(0, tz=UTC)) and existing_published_at is not None:
            published_val = existing_published_at
    else:
        h = stable_hash(item.url)[:6].upper()
        news_id = f"YP-{yymmdd}-{h}"

    metadata_dict = {}
    if getattr(item, "media_url", None):
        metadata_dict["media_url"] = item.media_url
    if getattr(item, "media_type", None):
        metadata_dict["media_type"] = item.media_type

    published_to_channel_at_val = None if is_valid_update else existing_published_to_channel_at

    return Article(
        id=news_id,
        title=normalize_headline(item.title),
        url=item.url,
        content=item.content.strip(),
        source=source,
        published_at=published_val,
        updated_at=updated_val,
        fetched_at=fetched_val,
        received_at=fetched_val,
        lifecycle_state=lifecycle_state,
        event_id=event_id,
        source_metadata=metadata_dict,
        published_to_channel_at=published_to_channel_at_val,
    )
