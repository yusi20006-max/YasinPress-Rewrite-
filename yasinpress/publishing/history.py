from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class DeliveryRecord:
    article_id: str
    destination: str
    success: bool
    attempts: int
    external_id: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class InMemoryDeliveryHistory:
    """Small storage-neutral history implementation; persistent storage can be plugged in later."""

    def __init__(self) -> None:
        self._records: list[DeliveryRecord] = []

    def add(self, record: DeliveryRecord) -> None:
        self._records.append(record)

    def all(self) -> tuple[DeliveryRecord, ...]:
        return tuple(self._records)

    def for_article(self, article_id: str) -> tuple[DeliveryRecord, ...]:
        return tuple(r for r in self._records if r.article_id == article_id)
