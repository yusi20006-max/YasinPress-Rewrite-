from datetime import UTC, datetime

from yasinpress.monitoring import OperationalReport


def test_report_contains_all_operational_dimensions():
    report = OperationalReport(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        received=20,
        accepted=15,
        rejected=2,
        expired=1,
        duplicates=2,
        queue_depth=4,
        published=10,
        failed=1,
        retrying=2,
        ai_processed=12,
        ai_modified=8,
        sources_total=6,
        sources_active=4,
        sources_inactive=1,
        sources_degraded=1,
        internet_ok=True,
        publisher_ok=True,
        scheduler_ok=True,
        watchdog_ok=True,
        uptime_seconds=3600,
    )
    data = report.as_dict()
    assert data["received"] == 20
    assert data["queue_depth"] == 4
    assert data["sources_inactive"] == 1
    assert data["internet_ok"] is True
    assert data["watchdog_ok"] is True


def test_text_report_is_safe_and_human_readable():
    report = OperationalReport(received=3, internet_ok=True)
    text = report.to_text()
    assert "received=3" in text
    assert "internet=OK" in text
    assert "YasinPress hourly report" in text
