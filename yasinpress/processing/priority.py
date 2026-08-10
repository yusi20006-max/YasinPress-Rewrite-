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
    high = sum(text.count(term.casefold()) for term in _HIGH)
    medium = sum(text.count(term.casefold()) for term in _MEDIUM)
    score = min(100, high * 30 + medium * 10)
    if score >= 60:
        level = "high"
    elif score >= 20:
        level = "medium"
    else:
        level = "normal"
    return PriorityResult(score=score, level=level)
