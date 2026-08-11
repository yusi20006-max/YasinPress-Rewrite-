from __future__ import annotations

from datetime import UTC, datetime, timedelta


DEFAULT_MAX_AGE = timedelta(hours=12)


def is_fresh(
    published_at: datetime | None,
    *,
    now: datetime | None = None,
    max_age: timedelta = DEFAULT_MAX_AGE,
) -> bool:
    """Return True when an article is within the normal publication age window."""
    if published_at is None:
        return False

    current = now or datetime.now(UTC)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=UTC)
    else:
        published_at = published_at.astimezone(UTC)

    if published_at > current:
        return True
    return current - published_at <= max_age
