from datetime import UTC, datetime, timedelta

from yasinpress.processing.breaking import detect_breaking


def test_breaking_news_is_detected_when_fresh():
    result = detect_breaking(
        "فوری: زلزله شدید",
        published_at=datetime.now(UTC) - timedelta(minutes=10),
    )
    assert result.is_breaking
    assert result.score >= 60


def test_urgency_wording_without_severity_does_not_make_news_breaking():
    result = detect_breaking(
        "فوری: جلسه خبری دولت",
        published_at=datetime.now(UTC) - timedelta(minutes=10),
    )
    assert not result.is_breaking


def test_priority_alone_does_not_make_news_breaking():
    result = detect_breaking(
        "قیمت بازار و هشدار اقتصادی",
        published_at=datetime.now(UTC) - timedelta(minutes=10),
    )
    assert not result.is_breaking


def test_old_severe_news_is_not_breaking():
    result = detect_breaking(
        "فوری: زلزله شدید",
        published_at=datetime.now(UTC) - timedelta(hours=13),
    )
    assert not result.is_breaking


def test_regular_news_is_not_breaking():
    result = detect_breaking(
        "گزارش روزانه فناوری",
        published_at=datetime.now(UTC) - timedelta(minutes=10),
    )
    assert not result.is_breaking
