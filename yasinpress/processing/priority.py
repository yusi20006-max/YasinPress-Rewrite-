from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PriorityResult:
    score: int
    level: str


_HIGH = ("فوری", "فوق العاده مهم", "breaking", "زلزله", "انفجار", "جنگ", "ترور")
_MEDIUM = ("مهم", "هشدار", "بحران", "تحریم", "انتخابات", "بازار", "قیمت")


def calculate_priority(title: str, content: str = "") -> PriorityResult:
    """Return the canonical queue priority contract.

    Queue consumers use four ordered levels: breaking, urgent, important, normal.
    ``score`` remains deterministic and bounded for metrics/debugging.
    """
    text = f"{title} {content}".casefold()
    high_hits = sum(term.casefold() in text for term in _HIGH)
    medium_hits = sum(term.casefold() in text for term in _MEDIUM)

    score = min(100, high_hits * 60 + min(medium_hits, 2) * 10)
    if "breaking" in text or high_hits >= 2:
        level = "breaking"
    elif high_hits == 1:
        level = "urgent"
    elif medium_hits > 0:
        level = "important"
    else:
        level = "normal"
    return PriorityResult(score=score, level=level)
