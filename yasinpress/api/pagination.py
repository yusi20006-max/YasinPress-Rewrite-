"""Shared pagination and filter normalization for collection endpoints."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    """Validated pagination parameters."""

    number: int = 1
    size: int = 25

    @property
    def offset(self) -> int:
        return (self.number - 1) * self.size

    @classmethod
    def from_query(cls, page: str | None = None, size: str | None = None, *, max_size: int = 100) -> "Page":
        try:
            number = int(page or 1)
        except ValueError:
            number = 1
        try:
            requested_size = int(size or 25)
        except ValueError:
            requested_size = 25
        return cls(max(1, number), min(max_size, max(1, requested_size)))


@dataclass(frozen=True)
class CollectionPage:
    items: list[dict[str, object]]
    page: Page
    total: int

    def as_dict(self) -> dict[str, object]:
        pages = (self.total + self.page.size - 1) // self.page.size
        return {"items": self.items, "pagination": {"page": self.page.number, "size": self.page.size, "total": self.total, "pages": pages}}
