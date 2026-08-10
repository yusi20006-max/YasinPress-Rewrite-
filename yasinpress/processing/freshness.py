from __future__ import annotations

from datetime import datetime, timedelta, timezone


def is_fresh(published_at: datetime | None, *, now: datetime | None = None, max_age: timedelta = timedelta(hours=24)) -> bool:
    """Return True when an article timestamp is within the allowed age window."""
    if published_at is None:
        return False

    current = now or datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    else:
        published_at = published_at.astimezone(timezone.utc)

    if published_at > current:
        return True
    return current - published_at <= max_age
