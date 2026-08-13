from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

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
    """Detect breaking news using explicit signals, severity and recency.

    Priority remains an input signal, but a priority score by itself cannot make
    an article breaking. The optional ``published_at`` keeps the public API
    backward compatible for callers that do not have publication metadata.
    """
    result = calculate_priority(title, content)
    text = f"{title} {content}".casefold()
    explicit = any(term.casefold() in text for term in _EXPLICIT_BREAKING)
    severe = any(term.casefold() in text for term in _SEVERE_EVENTS)
    age_hours = _age_hours(published_at)
    recent = age_hours is not None and age_hours <= 12

    # Explicit newsroom wording is sufficient when the item is fresh.
    # A severe event needs both recency and a meaningful priority signal.
    if explicit and recent:
        is_breaking = True
    elif severe and recent and result.score >= 60:
        is_breaking = True
    else:
        is_breaking = False

    return BreakingResult(is_breaking=is_breaking, score=result.score)
