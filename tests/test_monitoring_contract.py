from datetime import UTC, datetime

from yasinpress.monitoring import RuntimeSnapshot, hourly_report


def test_hourly_report_is_json_safe_and_complete():
    snapshot = RuntimeSnapshot(
        captured_at=datetime(2026, 8, 12, 12, 0, tzinfo=UTC),
        queue_pending=3,
        queue_processing=1,
        queue_retrying=2,
        queue_failed=4,
        queue_dead_letter=5,
        published_last_hour=6,
        source_health={"bbc": {"status": "healthy"}},
    )
    report = hourly_report(snapshot)
    assert report["timestamp"] == "2026-08-12T12:00:00+00:00"
    assert report["published_last_hour"] == 6
    assert report["queue"] == {
        "pending": 3,
        "processing": 1,
        "retrying": 2,
        "failed": 4,
        "dead_letter": 5,
    }
    assert report["source_health"]["bbc"]["status"] == "healthy"
