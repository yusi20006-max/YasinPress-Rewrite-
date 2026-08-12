from __future__ import annotations

from datetime import UTC, datetime, timedelta


def is_fresh(
    published_at: datetime | None,
    *,
    now: datetime | None = None,
    max_age: timedelta = timedelta(hours=12),
    is_breaking: bool = False,
    breaking_max_age: timedelta = timedelta(hours=24),
    allow_breaking_exemption: bool = True,
) -> bool:
    """Return True when an article timestamp is within the allowed age window."""
    if published_at is None:
        return False

    current = now or datetime.now(UTC)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=UTC)
    else:
        published_at = published_at.astimezone(UTC)

    if published_at > current:
        return True

    effective_max_age = max_age
    if is_breaking and allow_breaking_exemption:
        effective_max_age = breaking_max_age

    return current - published_at <= effective_max_age
