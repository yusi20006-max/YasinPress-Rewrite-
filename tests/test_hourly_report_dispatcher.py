from datetime import UTC, datetime, timedelta

from yasinpress.monitoring.dispatcher import HourlyReportDispatcher


class Queue:
    def metrics(self):
        return {"pending": 2, "processing": 1, "retrying": 0, "failed": 0, "dead_letter": 0, "published_last_hour": 3}

    def source_health(self):
        return {"source-a": {"status": "healthy"}}


def test_dispatch_is_limited_to_interval():
    sent = []
    dispatcher = HourlyReportDispatcher(sent.append)
    first = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
    assert dispatcher.dispatch(Queue(), now=first).success
    assert dispatcher.dispatch(Queue(), now=first + timedelta(minutes=30)) is None
    assert dispatcher.dispatch(Queue(), now=first + timedelta(hours=1)).success
    assert len(sent) == 2


def test_delivery_failure_does_not_advance_schedule():
    calls = 0

    def sender(_):
        nonlocal calls
        calls += 1
        raise RuntimeError("offline")

    dispatcher = HourlyReportDispatcher(sender)
    now = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
    result = dispatcher.dispatch(Queue(), now=now)
    assert result is not None and not result.success
    assert dispatcher.last_sent_at is None
    assert calls == 1
