"""Async helpers."""
import asyncio
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")

async def gather_limited(limit: int, tasks: list[Awaitable[T]]) -> list[T]:
    """Gather awaitables with a concurrency limit."""
    semaphore = asyncio.Semaphore(limit)
    async def run(task: Awaitable[T]) -> T:
        async with semaphore:
            return await task
    return await asyncio.gather(*(run(task) for task in tasks))
