from yasinpress.processing.classifier import classify


def test_pipeline_classifier_returns_stable_category_id():
    assert classify("خبر فناوری و هوش مصنوعی") == "technology"
    assert classify("خبر فوتبال و لیگ برتر") == "sports"
    assert classify("خبر تازه امروز") == "general"
