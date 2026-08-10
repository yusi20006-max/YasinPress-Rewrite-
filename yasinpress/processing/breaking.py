from __future__ import annotations

from dataclasses import dataclass

from .priority import calculate_priority


@dataclass(frozen=True)
class BreakingResult:
    is_breaking: bool
    score: int


def detect_breaking(title: str, content: str = "") -> BreakingResult:
    result = calculate_priority(title, content)
    return BreakingResult(is_breaking=result.score >= 60, score=result.score)
