from datetime import UTC, datetime, timedelta

from yasinpress.processing.freshness import is_fresh


def test_recent_article_is_fresh():
    now = datetime(2026, 1, 2, 12, tzinfo=UTC)
    assert is_fresh(now - timedelta(hours=11, minutes=59), now=now)


def test_article_at_12_hour_boundary_is_fresh():
    now = datetime(2026, 1, 2, 12, tzinfo=UTC)
    assert is_fresh(now - timedelta(hours=12), now=now)


def test_article_older_than_12_hours_is_not_fresh():
    now = datetime(2026, 1, 2, 12, tzinfo=UTC)
    assert not is_fresh(now - timedelta(hours=12, seconds=1), now=now)


def test_missing_timestamp_is_not_fresh():
    assert not is_fresh(None)


def test_naive_timestamp_is_treated_as_utc():
    now = datetime(2026, 1, 2, 12, tzinfo=UTC)
    assert is_fresh(datetime(2026, 1, 2, 11), now=now)
