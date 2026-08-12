from datetime import UTC, datetime, timedelta
from threading import Thread

import pytest

from yasinpress.scheduler import Scheduler


def test_scheduler_runs_deterministic_number_of_ticks():
    calls = []
    scheduler = Scheduler(lambda: calls.append(1) or "ok", interval=timedelta(seconds=1))
    assert scheduler.run(max_ticks=3) == 3
    assert calls == [1, 1, 1]
    assert scheduler.ticks == 3


def test_scheduler_stop_is_graceful():
    scheduler = Scheduler(lambda: None)
    scheduler.stop()
    assert scheduler.run(max_ticks=2) == 0
    assert scheduler.stopped


def test_scheduler_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        Scheduler(lambda: None, interval=timedelta(0))
    with pytest.raises(ValueError):
        Scheduler(lambda: None).run(max_ticks=-1)


def test_scheduler_failure_updates_watchdog_without_raising():
    scheduler = Scheduler(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    result = scheduler.run_once(datetime(2026, 1, 1, tzinfo=UTC))
    assert result is None
    assert scheduler.last_error == "boom"
    assert scheduler.watchdog.status(datetime(2026, 1, 1, tzinfo=UTC)).consecutive_failures == 1


def test_scheduler_prevents_overlapping_ticks():
    entered = []
    release = __import__("threading").Event()

    def tick():
        entered.append(1)
        release.wait(1)

    scheduler = Scheduler(tick)
    first = Thread(target=scheduler.run_once)
    first.start()
    while not entered:
        pass
    assert scheduler.run_once() is None
    release.set()
    first.join()
