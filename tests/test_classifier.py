from yasinpress.processing.classifier import PersianClassifier


def test_classifies_technology():
    result = PersianClassifier().classify("هوش مصنوعی جدید مایکروسافت معرفی شد")
    assert result.category == "فناوری"
    assert result.score > 0


def test_classifies_sports():
    result = PersianClassifier().classify("نتیجه بازی فوتبال لیگ برتر")
    assert result.category == "ورزشی"


def test_defaults_to_general():
    result = PersianClassifier().classify("خبر تازه امروز")
    assert result.category == "عمومی"
    assert result.score == 0


def test_content_can_affect_classification():
    result = PersianClassifier().classify("خبر جدید", "قیمت دلار و تورم افزایش یافت")
    assert result.category == "اقتصادی"
