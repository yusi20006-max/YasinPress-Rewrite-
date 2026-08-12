from datetime import UTC, datetime, timedelta

import pytest

from yasinpress.watchdog import Watchdog


def test_watchdog_marks_never_started_runtime_stale():
    watchdog = Watchdog()
    status = watchdog.status(datetime(2026, 1, 1, tzinfo=UTC))
    assert status.stale
    assert not status.healthy


def test_watchdog_recovers_after_success():
    watchdog = Watchdog(stale_after=timedelta(minutes=2))
    now = datetime(2026, 1, 1, tzinfo=UTC)
    watchdog.record_failure("temporary", now)
    assert not watchdog.status(now).healthy
    watchdog.record_success(now + timedelta(seconds=1))
    status = watchdog.status(now + timedelta(seconds=2))
    assert status.healthy
    assert not status.stale
    assert status.consecutive_failures == 0
    assert status.last_error is None


def test_watchdog_handles_naive_timestamp_as_utc():
    watchdog = Watchdog()
    watchdog.record_success(datetime(2026, 1, 1))
    assert watchdog.status(datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC)).healthy


def test_watchdog_rejects_invalid_stale_window():
    with pytest.raises(ValueError):
        Watchdog(timedelta(0))
