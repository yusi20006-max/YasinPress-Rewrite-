from datetime import UTC, datetime

from yasinpress.monitoring import RuntimeSnapshot, hourly_report


def test_hourly_report_has_stable_queue_contract():
    snapshot = RuntimeSnapshot(
        captured_at=datetime(2026, 1, 1, tzinfo=UTC),
        queue_pending=3,
        queue_processing=1,
        queue_retrying=2,
        queue_failed=1,
        queue_dead_letter=4,
        published_last_hour=7,
        source_health={"bbc": {"status": "healthy"}},
    )
    report = hourly_report(snapshot)
    assert report["published_last_hour"] == 7
    assert report["queue"]["pending"] == 3
    assert report["queue"]["dead_letter"] == 4
    assert report["source_health"]["bbc"]["status"] == "healthy"
