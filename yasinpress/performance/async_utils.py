"""Async helpers."""

import asyncio
from collections.abc import Awaitable


async def gather_limited[T](limit: int, tasks: list[Awaitable[T]]) -> list[T]:
    """Gather awaitables with a concurrency limit."""
    semaphore = asyncio.Semaphore(limit)

    async def run(task: Awaitable[T]) -> T:
        async with semaphore:
            return await task

    return await asyncio.gather(*(run(task) for task in tasks))
