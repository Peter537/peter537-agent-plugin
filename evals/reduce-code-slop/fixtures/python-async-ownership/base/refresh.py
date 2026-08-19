import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar


T = TypeVar("T")


async def refresh_once(fetch: Callable[[], Awaitable[T]]) -> T:
    task = asyncio.create_task(fetch())
    return await task
