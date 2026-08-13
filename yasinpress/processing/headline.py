"""Headline normalization logic."""


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
                    # To avoid stripping quotes from legitimate speaker attributions (e.g. "بایدن؛ «...»")
                    # we only strip if the left part is long enough (at least 3 words and 10 characters).
                    words = left.split()
                    if len(words) >= 3 and len(left) >= 10:
                        title = left
                        break

    return title
