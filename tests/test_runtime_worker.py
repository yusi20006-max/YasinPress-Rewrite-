from datetime import UTC, datetime, timedelta

import pytest

from yasinpress.runtime_worker import PublicationWorker


class Queue:
    def __init__(self):
        self.recovered = 0

    def recover_expired_leases(self, now):
        self.recovered += 1
        return 0


def test_worker_recovers_leases_before_publishing():
    queue = Queue()
    calls = []
    worker = PublicationWorker(queue, lambda: calls.append("publish") or "ok")
    result = worker.tick(datetime(2026, 1, 1, tzinfo=UTC))
    assert result == "ok"
    assert queue.recovered == 1
    assert calls == ["publish"]
    assert worker.last_tick_at is not None


def test_worker_rejects_invalid_run_window():
    worker = PublicationWorker(Queue(), lambda: None)
    with pytest.raises(ValueError):
        worker.run_for(timedelta(0))


def test_worker_runs_multiple_ticks_for_bounded_window():
    queue = Queue()
    calls = []
    worker = PublicationWorker(queue, lambda: calls.append("publish"))
    ticks = worker.run_for(timedelta(milliseconds=5), timedelta(milliseconds=1))
    assert ticks >= 2
    assert worker.tick_count == ticks
    assert queue.recovered == ticks
    assert len(calls) == ticks
