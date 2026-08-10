from yasinpress.processing.breaking import detect_breaking


def test_breaking_news_is_detected():
    result = detect_breaking("فوری: زلزله شدید")
    assert result.is_breaking
    assert result.score >= 60


def test_regular_news_is_not_breaking():
    result = detect_breaking("گزارش روزانه فناوری")
    assert not result.is_breaking
