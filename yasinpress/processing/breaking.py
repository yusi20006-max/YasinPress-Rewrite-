from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from .priority import calculate_priority


@dataclass(frozen=True)
class BreakingResult:
    is_breaking: bool
    score: int


# Explicit newsroom signals. A priority score alone is intentionally not enough.
_EXPLICIT_BREAKING = (
    "خبر فوری",
    "فوری",
    "لحظاتی پیش",
    "breaking",
    "urgent",
)
_SEVERE_EVENTS = (
    "زلزله",
    "انفجار",
    "حمله",
    "ترور",
    "جنگ",
    "آتش سوزی",
    "آتش‌سوزی",
    "سقوط هواپیما",
    "هواپیما سقوط",
)


def _age_hours(published_at: datetime | None) -> float | None:
    if published_at is None:
        return None
    published = published_at
    if published.tzinfo is None:
        published = published.replace(tzinfo=UTC)
    else:
        published = published.astimezone(UTC)
    age = datetime.now(UTC) - published
    return max(0.0, age.total_seconds() / 3600)


def detect_breaking(
    title: str,
    content: str = "",
    *,
    published_at: datetime | None = None,
) -> BreakingResult:
    """Detect breaking news from explicit urgency, title severity and recency."""
    result = calculate_priority(title, content)
    title_text = title.casefold()
    explicit = any(term.casefold() in title_text for term in _EXPLICIT_BREAKING)
    severe = any(term.casefold() in title_text for term in _SEVERE_EVENTS)
    age_hours = _age_hours(published_at)
    recent = age_hours is not None and age_hours <= 12

    # Body text can contain historical/contextual references such as
    # "جنگ تحمیلی". Severe-event detection therefore stays title-scoped.
    is_breaking = recent and (explicit or severe)
    return BreakingResult(is_breaking=is_breaking, score=result.score)
