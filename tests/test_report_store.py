import sqlite3
from datetime import UTC, datetime

from yasinpress.monitoring.report import OperationalReport
from yasinpress.monitoring.store import OperationalReportStore


def test_report_store_round_trip_and_hourly_history():
    db = sqlite3.connect(":memory:")
    store = OperationalReportStore(db)
    first = OperationalReport(
        timestamp=datetime(2026, 1, 1, 10, tzinfo=UTC),
        received=4,
        accepted=3,
        queue_depth=2,
        published=1,
        sources_total=5,
        sources_active=4,
        sources_inactive=1,
        internet_ok=True,
        publisher_ok=True,
        scheduler_ok=True,
        watchdog_ok=True,
    )
    second = OperationalReport(
        timestamp=datetime(2026, 1, 1, 11, tzinfo=UTC),
        received=7,
        accepted=5,
        queue_depth=3,
        published=2,
    )
    store.save(first)
    store.save(second)

    latest = store.latest()
    assert latest is not None
    assert latest.timestamp == second.timestamp
    assert latest.received == 7
    assert latest.queue_depth == 3

    history = store.hourly(24)
    assert [item.timestamp for item in history] == [second.timestamp, first.timestamp]


def test_report_store_upserts_same_timestamp():
    db = sqlite3.connect(":memory:")
    store = OperationalReportStore(db)
    timestamp = datetime(2026, 1, 1, 12, tzinfo=UTC)
    store.save(OperationalReport(timestamp=timestamp, received=1))
    store.save(OperationalReport(timestamp=timestamp, received=9))
    assert store.latest().received == 9
    assert len(store.hourly(24)) == 1
