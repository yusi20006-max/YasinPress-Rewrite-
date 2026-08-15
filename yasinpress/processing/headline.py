"""Headline normalization logic."""

from html import unescape
import re


_HTML_TAG_RE = re.compile(r"<\s*/?\s*[A-Za-z][^>]*>")
_MARKDOWN_CODE_RE = re.compile(r"`{1,3}")
# Preserve U+200C ZERO WIDTH NON-JOINER because it is semantic Persian
# orthography (e.g. «رئیس‌جمهور», «می‌خواست»). Remove only formatting bidi
# controls and other non-semantic zero-width characters.
_INVISIBLE_RE = re.compile(r"[\u200b\u200d\u200e\u200f\u202a-\u202e\u2066-\u2069]")


def _strip_title_markup(title: str) -> str:
    """Remove HTML/Markdown control markup without removing legitimate Latin words."""
    title = unescape(title)
    title = _HTML_TAG_RE.sub(" ", title)
    title = _MARKDOWN_CODE_RE.sub("", title)
    title = _INVISIBLE_RE.sub("", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def ends_with_speech_indicator(text: str) -> bool:
    """Check if the text ends with a common Persian or English speech-action verb."""
    speech_indicators = {
        "گفت", "افزود", "نوشت", "پرسید", "پاسخ داد", "اعلام کرد", "تاکید کرد", "تصریح کرد",
        "بیان کرد", "ابراز داشت", "خواستار شد", "عنوان کرد", "اظهار داشت", "مطرح کرد", "خبر داد",
        "آورده است", "توصیف کرد", "یادآور شد", "اعلام داشت", "دانست", "خواند", "خواست", "گفتند",
        "افزودند", "نوشتند", "پرسیدند", "اعلام کردند", "تاکید کردند", "تصریح کردند", "خواستار شدند",
        "اظهار داشتند", "خبر دادند", "توضیح داد", "توضیح دادند", "اشاره کرد", "اشاره کردند", "مدعی شد",
        "مدعی شدند", "اعلام نمود", "اعلام نمودند", "ابراز نمود", "ابراز نمودند", "ابراز کرد", "ابراز کردند",
        "خاطرنشان کرد", "خاطرنشان کردند", "متذکر شد", "متذکر شدند", "امیدواری کرد", "امیدواری کردند",
        "said", "says", "wrote", "reports", "stated", "claims", "adds", "argues", "warns", "urges",
        "asked", "replied", "commented", "told",
    }
    cleaned = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text).strip()
    words = cleaned.split()
    if not words:
        return False
    if words[-1].lower() in speech_indicators:
        return True
    return len(words) >= 2 and f"{words[-2]} {words[-1]}".lower() in speech_indicators


def normalize_headline(title: str) -> str:
    """Normalize a headline while preserving Latin names and Persian orthography."""
    title = _strip_title_markup(title)
    if not title:
        return ""

    known_suffixes = {
        "bbc news فارسی", "bbc news persian", "bbc persian", "bbc news", "bbc",
        "dw persian", "dw", "دی دبلیو", "euronews persian", "euronews", "یورونیوز",
        "france 24 persian", "france 24", "فرانس ۲۴", "voa persian", "voa", "صدای آمریکا",
        "irna", "ایرنا", "خبرگزاری ایرنا", "isna", "ایسنا", "خبرگزاری ایسنا",
        "mehr news", "mehr", "مهر", "خبرگزاری مهر", "tasnim", "تسنیم", "خبرگزاری تسنیم",
        "ilna", "ایلنا", "خبرگزاری ایلنا",
    }

    for sep in ("-", "|", "–", "—"):
        if sep in title:
            left, right = (part.strip() for part in title.rsplit(sep, 1))
            if right.lower() in known_suffixes:
                title = left
                break

    quote_pairs = [("«", "»"), ('"', '"'), ("'", "'"), ("“", "”"), ("‘", "’"), ("[", "]"), ("(", ")")]
    for sep in ("؛", ";", "-", "–", "—", "|"):
        if sep not in title:
            continue
        left, right = (part.strip() for part in title.rsplit(sep, 1))
        is_quoted = any(right.startswith(open_q) and right.endswith(close_q) for open_q, close_q in quote_pairs)
        if is_quoted and left and not ends_with_speech_indicator(left) and len(left.split()) >= 3 and len(left) >= 10:
            title = left
            break

    return title
