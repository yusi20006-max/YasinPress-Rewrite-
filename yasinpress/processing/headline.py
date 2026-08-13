"""Headline normalization logic."""

import re


def ends_with_speech_indicator(text: str) -> bool:
    """Check if the text ends with a common Persian or English speech-action verb."""
    speech_indicators = {
        # Persian speech/statement verbs & phrases
        "گفت",
        "افزود",
        "نوشت",
        "پرسید",
        "پاسخ داد",
        "اعلام کرد",
        "تاکید کرد",
        "تصریح کرد",
        "بیان کرد",
        "ابراز داشت",
        "خواستار شد",
        "عنوان کرد",
        "اظهار داشت",
        "مطرح کرد",
        "خبر داد",
        "آورده است",
        "توصیف کرد",
        "یادآور شد",
        "اعلام داشت",
        "دانست",
        "خواند",
        "خواست",
        "گفتند",
        "افزودند",
        "نوشتند",
        "پرسیدند",
        "اعلام کردند",
        "تاکید کردند",
        "تصریح کردند",
        "خواستار شدند",
        "اظهار داشتند",
        "خبر دادند",
        "توضیح داد",
        "توضیح دادند",
        "اشاره کرد",
        "اشاره کردند",
        "مدعی شد",
        "مدعی شدند",
        "اعلام نمود",
        "اعلام نمودند",
        "ابراز نمود",
        "ابراز نمودند",
        "ابراز کرد",
        "ابراز کردند",
        "خاطرنشان کرد",
        "خاطرنشان کردند",
        "متذکر شد",
        "متذکر شدند",
        "امیدواری کرد",
        "امیدواری کردند",
        # English speech verbs
        "said",
        "says",
        "wrote",
        "reports",
        "stated",
        "claims",
        "adds",
        "argues",
        "warns",
        "urges",
        "asked",
        "replied",
        "commented",
        "told",
    }

    # Normalize spacing and remove punctuation except letters/numbers and spaces
    cleaned = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text).strip()
    words = cleaned.split()
    if not words:
        return False

    # Check last word (case-insensitive for English)
    last_word = words[-1].lower()
    if last_word in speech_indicators:
        return True

    # Check last two words combined
    if len(words) >= 2:
        last_two = f"{words[-2]} {words[-1]}".lower()
        if last_two in speech_indicators:
            return True

    return False


def normalize_headline(title: str) -> str:
    """Normalize a headline to remove unwanted RSS subtitles, description quotes, or site suffixes."""
    if not title:
        return ""

    title = title.strip()
    if not title:
        return ""

    # 1. Detect and remove common RSS site suffixes at the end of the title.
    # Supported separators: '-', '|', '–', '—'
    known_suffixes = {
        "bbc news فارسی",
        "bbc news persian",
        "bbc persian",
        "bbc news",
        "bbc",
        "dw persian",
        "dw",
        "دی دبلیو",
        "euronews persian",
        "euronews",
        "یورونیوز",
        "france 24 persian",
        "france 24",
        "فرانس ۲۴",
        "voa persian",
        "voa",
        "صدای آمریکا",
        "irna",
        "ایرنا",
        "خبرگزاری ایرنا",
        "isna",
        "ایسنا",
        "خبرگزاری ایسنا",
        "mehr news",
        "mehr",
        "مهر",
        "خبرگزاری مهر",
        "tasnim",
        "تسنیم",
        "خبرگزاری تسنیم",
        "ilna",
        "ایلنا",
        "خبرگزاری ایلنا",
    }

    for sep in ("-", "|", "–", "—"):
        if sep in title:
            parts = title.rsplit(sep, 1)
            if len(parts) == 2:
                left, right = parts[0].strip(), parts[1].strip()
                if right.lower() in known_suffixes:
                    title = left
                    break

    # 2. Detect and remove descriptive/quoted subtitles separated by common separators.
    # Supported separators: '؛', ';', '-', '–', '—', '|'
    quote_pairs = [
        ("«", "»"),
        ('"', '"'),
        ("'", "'"),
        ("“", "”"),
        ("‘", "’"),
        ("[", "]"),
        ("(", ")"),
    ]

    for sep in ("؛", ";", "-", "–", "—", "|"):
        if sep in title:
            parts = title.rsplit(sep, 1)
            if len(parts) == 2:
                left, right = parts[0].strip(), parts[1].strip()

                is_quoted = False
                for open_q, close_q in quote_pairs:
                    if right.startswith(open_q) and right.endswith(close_q):
                        is_quoted = True
                        break

                if is_quoted and left:
                    # Do not strip if the left part ends with a speech verb/phrase,
                    # indicating a speaker attribution rather than a subtitle.
                    if ends_with_speech_indicator(left):
                        continue

                    # To avoid stripping quotes from legitimate speaker attributions (e.g. "بایدن؛ «...»")
                    # we only strip if the left part is long enough (at least 3 words and 10 characters).
                    words = left.split()
                    if len(words) >= 3 and len(left) >= 10:
                        title = left
                        break

    return title
