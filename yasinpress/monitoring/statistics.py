"""Statistics calculations."""


def average(values: list[float]) -> float:
    """Return arithmetic average."""
    return sum(values) / len(values) if values else 0.0
