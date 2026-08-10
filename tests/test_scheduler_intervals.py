from datetime import datetime, timedelta, timezone

from yasinpress.scheduler.queue import JobQueue
from yasinpress.scheduler.scheduler import Scheduler


def test_interval_scheduler_runs_due_tasks():
    now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    calls = []
    scheduler = Scheduler(JobQueue(), now=lambda: now[0])
    scheduler.add_interval("feed", timedelta(seconds=10), lambda: calls.append("feed"))
    scheduler.run_due()
    assert calls == ["feed"]
    now[0] += timedelta(seconds=9)
    scheduler.run_due()
    assert calls == ["feed"]
    now[0] += timedelta(seconds=1)
    scheduler.run_due()
    assert calls == ["feed", "feed"]
