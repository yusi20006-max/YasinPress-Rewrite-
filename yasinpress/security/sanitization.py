"""Input sanitization."""
import html


def sanitize_text(value: str) -> str:
    """Escape unsafe text."""
    return html.escape(value.strip(), quote=True)
