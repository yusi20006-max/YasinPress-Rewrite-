from __future__ import annotations

from datetime import UTC, datetime, timedelta


def is_fresh(
    published_at: datetime | None,
    *,
    now: datetime | None = None,
    max_age: timedelta = timedelta(hours=12),
    is_breaking: bool = False,
    allow_breaking_exemption: bool = False,
    breaking_max_age: timedelta = timedelta(hours=24),
) -> bool:
    """Return True only when an article is within the configured publication age window.

    The production contract is strict: articles older than ``max_age`` are not
    publishable, including breaking articles. The legacy breaking-exemption
    parameters remain accepted for API compatibility but are intentionally
    ignored so callers cannot bypass the freshness contract.
    """
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
