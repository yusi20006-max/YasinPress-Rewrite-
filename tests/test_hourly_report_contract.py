from datetime import UTC, datetime

from yasinpress.monitoring import RuntimeSnapshot, hourly_report


def test_hourly_report_is_json_safe_and_contains_required_operational_metrics():
    captured = datetime(2026, 1, 1, tzinfo=UTC)
    report = hourly_report(
        RuntimeSnapshot(
            captured_at=captured,
            queue_pending=3,
            queue_processing=1,
            queue_retrying=2,
            queue_failed=1,
            queue_dead_letter=4,
            published_last_hour=7,
            source_health={"bbc": {"status": "healthy"}},
        )
    )
    assert report["timestamp"] == captured.isoformat()
    assert report["published_last_hour"] == 7
    assert report["queue"]["dead_letter"] == 4
    assert report["source_health"]["bbc"]["status"] == "healthy"
