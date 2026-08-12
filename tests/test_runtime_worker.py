from datetime import UTC, datetime

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
