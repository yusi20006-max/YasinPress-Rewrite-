from datetime import UTC, datetime, timedelta

from yasinpress.processing.freshness import DEFAULT_MAX_AGE, is_fresh


def test_default_freshness_window_is_twelve_hours() -> None:
    assert DEFAULT_MAX_AGE == timedelta(hours=12)


def test_article_at_twelve_hours_is_fresh() -> None:
    now = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
    assert is_fresh(now - timedelta(hours=12), now=now)


def test_article_older_than_twelve_hours_is_stale() -> None:
    now = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
    assert not is_fresh(now - timedelta(hours=12, seconds=1), now=now)
