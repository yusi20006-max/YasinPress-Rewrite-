from datetime import UTC, datetime, timedelta

from yasinpress.processing.freshness import is_fresh


def test_recent_article_is_fresh():
    now = datetime(2026, 1, 2, 12, tzinfo=UTC)
    # With normal <=12h freshness, an article published 11 hours ago is fresh.
    assert is_fresh(now - timedelta(hours=11), now=now)


def test_article_at_boundary_is_fresh():
    now = datetime(2026, 1, 2, 12, tzinfo=UTC)
    # Exact boundary (12h) is fresh.
    assert is_fresh(now - timedelta(hours=12), now=now)


def test_old_article_is_not_fresh():
    now = datetime(2026, 1, 2, 12, tzinfo=UTC)
    # Older than 12h is not fresh for normal articles.
    assert not is_fresh(now - timedelta(hours=12, seconds=1), now=now)


def test_breaking_article_exemption_is_fresh():
    now = datetime(2026, 1, 2, 12, tzinfo=UTC)
    # A breaking article published 23 hours ago is still fresh with breaking exemption (default limit 24h).
    assert is_fresh(now - timedelta(hours=23), now=now, is_breaking=True)
    # A breaking article at 24h is still fresh.
    assert is_fresh(now - timedelta(hours=24), now=now, is_breaking=True)
    # A breaking article older than 24h is not fresh.
    assert not is_fresh(now - timedelta(hours=24, seconds=1), now=now, is_breaking=True)


def test_missing_timestamp_is_not_fresh():
    assert not is_fresh(None)


def test_naive_timestamp_is_treated_as_utc():
    now = datetime(2026, 1, 2, 12, tzinfo=UTC)
    assert is_fresh(datetime(2026, 1, 2, 11), now=now)  # noqa: DTZ001 - intentional naive timestamp contract
