from datetime import datetime, timedelta, timezone

from yasinpress.scheduler.scheduler import Scheduler


def test_scheduler_does_not_skip_next_interval_after_multiple_ticks():
    current = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    calls = []
    scheduler = Scheduler(type("Q", (), {})(), now=lambda: current[0])
    scheduler.add_interval("feed", timedelta(seconds=10), lambda: calls.append(current[0]))

    scheduler.run_due()
    current[0] += timedelta(seconds=10)
    scheduler.run_due()
    current[0] += timedelta(seconds=10)
    scheduler.run_due()

    assert len(calls) == 3


def test_scheduler_rejects_invalid_interval():
    scheduler = Scheduler(type("Q", (), {})())
    try:
        scheduler.add_interval("bad", timedelta(seconds=0), lambda: None)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
