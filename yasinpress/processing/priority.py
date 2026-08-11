from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PriorityResult:
    score: int
    level: str


_HIGH = ("فوری", "فوق العاده مهم", "breaking", "زلزله", "انفجار", "جنگ", "ترور")
_MEDIUM = ("مهم", "هشدار", "بحران", "تحریم", "انتخابات", "بازار", "قیمت")


def calculate_priority(title: str, content: str = "") -> PriorityResult:
    text = f"{title} {content}".casefold()
    high = sum(term.casefold() in text for term in _HIGH)
    medium = sum(term.casefold() in text for term in _MEDIUM)
    score = min(100, high * 60 + min(medium, 2) * 10)
    if high > 0 or score >= 40:
        level = "high"
    elif score >= 20:
        level = "medium"
    else:
        level = "normal"
    return PriorityResult(score=score, level=level)
