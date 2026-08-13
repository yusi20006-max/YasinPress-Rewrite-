from yasinpress.processing.priority import calculate_priority


def test_normal_priority():
    result = calculate_priority("خبر روزانه")
    assert result.level == "normal"
    assert result.score == 0


def test_important_priority():
    result = calculate_priority("هشدار درباره قیمت بازار")
    assert result.level == "important"
    assert result.score == 20


def test_urgent_priority():
    result = calculate_priority("فوری: زلزله")
    assert result.level == "urgent"
    assert result.score == 60


def test_breaking_priority():
    result = calculate_priority("زلزله و انفجار")
    assert result.level == "breaking"
    assert result.score == 100
