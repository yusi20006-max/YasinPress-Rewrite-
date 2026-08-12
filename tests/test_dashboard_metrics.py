from datetime import UTC, datetime

from yasinpress.monitoring import RuntimeSnapshot
from yasinpress.monitoring.metrics import dashboard_metrics


def test_dashboard_metrics_is_json_safe_and_groups_queue_state():
    captured = datetime(2026, 1, 1, tzinfo=UTC)
    data = dashboard_metrics(RuntimeSnapshot(captured, 2, 1, 3, 4, 5, 6, {"rss": {"status": "healthy"}}))
    assert data["captured_at"] == captured.isoformat()
    assert data["queue"] == {
        "pending": 2,
        "processing": 1,
        "retrying": 3,
        "failed": 4,
        "dead_letter": 5,
    }
    assert data["published_last_hour"] == 6
    assert "queue_pending" not in data
