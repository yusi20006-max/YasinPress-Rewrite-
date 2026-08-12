from datetime import UTC, datetime, timedelta

from yasinpress.watchdog import Watchdog


def test_watchdog_recovers_after_success():
    watchdog = Watchdog()
    now = datetime(2026, 1, 1, tzinfo=UTC)
    watchdog.record_success(now)
    assert watchdog.status(now).healthy
    assert watchdog.status(now).consecutive_failures == 0


def test_watchdog_exposes_failures_and_stale_state():
    watchdog = Watchdog(stale_after=timedelta(seconds=30))
    now = datetime(2026, 1, 1, tzinfo=UTC)
    watchdog.record_failure("worker failed", now)
    assert not watchdog.status(now).healthy
    assert watchdog.status(now).consecutive_failures == 1
    watchdog.record_success(now + timedelta(seconds=1))
    assert watchdog.status(now + timedelta(seconds=1)).healthy
