"""Content cleaning."""

import html
import re


def clean_html(text: str) -> str:
    """Remove simple HTML tags and normalize whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(text))).strip()
