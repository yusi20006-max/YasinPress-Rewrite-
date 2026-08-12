from yasinpress.processing.priority import calculate_priority


def test_priority_contract_has_four_queue_levels():
    assert calculate_priority("خبر عادی").level == "normal"
    assert calculate_priority("افزایش قیمت بازار").level == "important"
    assert calculate_priority("جنگ در منطقه").level == "urgent"
    assert calculate_priority("breaking: زلزله شدید").level == "breaking"


def test_priority_is_deterministic_and_bounded():
    result = calculate_priority("زلزله جنگ انفجار ترور", "بحران تحریم")
    assert 0 <= result.score <= 100
    assert result.level == "breaking"
