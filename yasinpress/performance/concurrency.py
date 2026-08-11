"""Concurrency utilities."""

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor


def parallel_map[T, R](func: Callable[[T], R], values: Iterable[T], max_workers: int = 4) -> list[R]:
    """Map a function concurrently."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(func, values))
