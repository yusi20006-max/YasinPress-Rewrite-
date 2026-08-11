"""Rule-based categorization."""


class Categorizer:
    """Assign categories from content."""

    def categorize(self, text: str) -> str:
        """Return a category label."""
        lowered = text.lower()
        if "sport" in lowered:
            return "sports"
        if "econom" in lowered or "market" in lowered:
            return "economy"
        return "general"
