"""Tag generation."""

import re


class TagEngine:
    """Extract publication tags."""

    def tags(self, text: str, limit: int = 5) -> list[str]:
        """Return normalized tags from frequent words."""
        words = [w.lower() for w in re.findall(r"[A-Za-z]{4,}", text)]
        return list(dict.fromkeys(words))[:limit]
