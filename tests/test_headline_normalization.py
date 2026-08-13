"""Unit and regression tests for headline normalization."""

from yasinpress.processing.headline import normalize_headline


def test_regression_case_1():
    """Case 1: Semicolon followed by quoted/descriptive subtitle."""
    input_headline = "پنج سال حکومت طالبان؛ «قابله‌ام و باردار... برای آینده دخترم نگرانم»"
    expected = "پنج سال حکومت طالبان"
    assert normalize_headline(input_headline) == expected


def test_regression_case_2():
    """Case 2: Legitimate Persian question must remain unchanged."""
    input_headline = "کارتاز چه بود و چرا ۵۰۰ سال پیش عبور از تنگه هرمز مجوز می‌خواست؟"
    assert normalize_headline(input_headline) == input_headline


def test_normal_persian_headline():
    """Normal Persian headline remains unchanged."""
    headline = "سفر وزیر امور خارجه به مسکو"
    assert normalize_headline(headline) == headline


def test_persian_headline_containing_semicolon_no_quotes():
    """Persian headline containing '؛' but no quotes/noise remains unchanged."""
    headline = "سیل در سیستان؛ خسارت‌ها و امدادرسانی"
    assert normalize_headline(headline) == headline


def test_persian_headline_containing_colon():
    """Persian headline containing ':' (no quotes) remains unchanged."""
    headline = "فوری: زلزله شدید در تهران"
    assert normalize_headline(headline) == headline


def test_persian_headline_containing_question():
    """Persian headline containing '؟' remains unchanged."""
    headline = "آیا فردا مدارس تهران تعطیل است؟"
    assert normalize_headline(headline) == headline


def test_headline_containing_quotation_marks():
    """Headline containing quotation marks should preserve valid quotes/attribution."""
    # Attribution/legitimate quotation
    headline = "رئیس‌جمهور: «برنامه هسته‌ای ما صلح‌آمیز است»"
    assert normalize_headline(headline) == headline

    # Short speaker attribution with semicolon should not be stripped
    headline_short = "بایدن؛ «با قدرت ادامه می‌دهیم»"
    assert normalize_headline(headline_short) == headline_short


def test_english_headline():
    """English headline with or without separator."""
    headline = "Major breakthrough in quantum computing"
    assert normalize_headline(headline) == headline

    # English headline with known site suffix removed
    headline_with_suffix = "Major breakthrough in quantum computing - BBC News"
    assert normalize_headline(headline_with_suffix) == "Major breakthrough in quantum computing"


def test_empty_or_whitespace_title():
    """Empty or whitespace title returns empty string."""
    assert normalize_headline("") == ""
    assert normalize_headline("    ") == ""


def test_already_clean_title():
    """Already-clean title remains unchanged."""
    headline = "This is a clean headline"
    assert normalize_headline(headline) == headline


def test_normalization_no_change_needed():
    """Title where normalization must make no change."""
    headline = "بحران آب در خاورمیانه و شمال آفریقا"
    assert normalize_headline(headline) == headline


def test_confirmed_rss_metadata_noise():
    """Title containing RSS metadata/noise from confirmed feeds."""
    # Test removing BBC Persian suffix
    headline_bbc = "تنش در خاورمیانه؛ درخواست خویشتن‌داری از سوی جامعه جهانی - BBC News فارسی"
    # Should strip the BBC suffix first, then see the semicolon + quotes check is not matched, so output:
    # "تنش در خاورمیانه؛ درخواست خویشتن‌داری از سوی جامعه جهانی"
    assert normalize_headline(headline_bbc) == "تنش در خاورمیانه؛ درخواست خویشتن‌داری از سوی جامعه جهانی"

    # Test removing Mehr News suffix
    headline_mehr = "پایان رزمایش هوایی مدافعان آسمان ولایت - خبرگزاری مهر"
    assert normalize_headline(headline_mehr) == "پایان رزمایش هوایی مدافعان آسمان ولایت"

    # Test Euronews suffix
    headline_euronews = "توافق جدید تجاری بین بریتانیا و اتحادیه اروپا | یورونیوز"
    assert normalize_headline(headline_euronews) == "توافق جدید تجاری بین بریتانیا و اتحادیه اروپا"
