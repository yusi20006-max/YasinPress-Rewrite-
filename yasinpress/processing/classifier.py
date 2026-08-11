from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Classification:
    category: str
    score: float


DEFAULT_RULES: dict[str, tuple[str, ...]] = {
    "فناوری": ("هوش مصنوعی", "هوش مصنوعی", "فناوری", "تکنولوژی", "اپل", "گوگل", "مایکروسافت", "سامسونگ", "نرم افزار", "اینترنت"),
    "اقتصادی": ("اقتصاد", "دلار", "ارز", "بورس", "بانک", "تورم", "قیمت", "بازار", "سهام"),
    "سیاسی": ("دولت", "مجلس", "رئیس جمهور", "ریاست جمهوری", "وزیر", "انتخابات", "تحریم", "سیاست"),
    "ورزشی": ("فوتبال", "ورزش", "المپیک", "جام جهانی", "لیگ", "پرسپولیس", "استقلال", "بسکتبال"),
    "فرهنگی": ("سینما", "فیلم", "کتاب", "موسیقی", "هنر", "فرهنگ", "بازیگر"),
    "علمی": ("علم", "پژوهش", "دانشمند", "فضا", "ناسا", "پزشکی", "آزمایشگاه"),
    "بین‌الملل": ("آمریکا", "اروپا", "روسیه", "اوکراین", "چین", "اسرائیل", "غزه", "سازمان ملل"),
    "اجتماعی": ("جامعه", "اجتماعی", "آموزش", "مدرسه", "دانشگاه", "حوادث", "شهری"),
}


CATEGORY_IDS: dict[str, str] = {
    "فناوری": "technology",
    "اقتصادی": "economy",
    "سیاسی": "politics",
    "ورزشی": "sports",
    "فرهنگی": "culture",
    "علمی": "science",
    "بین‌الملل": "international",
    "اجتماعی": "social",
    "عمومی": "general",
}


class PersianClassifier:
    def __init__(self, rules: dict[str, tuple[str, ...]] | None = None) -> None:
        self.rules = rules or DEFAULT_RULES

    def classify(self, title: str, content: str = "") -> Classification:
        text = f"{title} {content}".casefold()
        best_category = "عمومی"
        best_hits = 0
        for category, keywords in self.rules.items():
            hits = sum(1 for keyword in keywords if keyword.casefold() in text)
            if hits > best_hits:
                best_category, best_hits = category, hits
        score = min(1.0, best_hits / 3) if best_hits else 0.0
        return Classification(best_category, score)


def classify(title: str, content: str = "") -> str:
    """Return the stable English category identifier used by Article."""
    result = PersianClassifier().classify(title, content)
    return CATEGORY_IDS[result.category]
