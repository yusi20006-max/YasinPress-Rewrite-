from datetime import datetime, timedelta, timezone

from yasinpress.processing.freshness import is_fresh


def test_recent_article_is_fresh():
    now = datetime(2026, 1, 2, 12, tzinfo=timezone.utc)
    assert is_fresh(now - timedelta(hours=23), now=now)


def test_article_at_boundary_is_fresh():
    now = datetime(2026, 1, 2, 12, tzinfo=timezone.utc)
    assert is_fresh(now - timedelta(hours=24), now=now)


def test_old_article_is_not_fresh():
    now = datetime(2026, 1, 2, 12, tzinfo=timezone.utc)
    assert not is_fresh(now - timedelta(hours=24, seconds=1), now=now)


def test_missing_timestamp_is_not_fresh():
    assert not is_fresh(None)


def test_naive_timestamp_is_treated_as_utc():
    now = datetime(2026, 1, 2, 12, tzinfo=timezone.utc)
    assert is_fresh(datetime(2026, 1, 2, 11), now=now)
