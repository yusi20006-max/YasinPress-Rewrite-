from yasinpress.processing.priority import calculate_priority


def test_normal_priority():
    result = calculate_priority("خبر روزانه")
    assert result.level == "normal"
    assert result.score == 0


def test_medium_priority():
    result = calculate_priority("هشدار درباره قیمت بازار")
    assert result.level == "important"
    assert result.score == 20


def test_high_priority():
    result = calculate_priority("فوری: زلزله و انفجار")
    assert result.level == "breaking"
    assert result.score >= 60
