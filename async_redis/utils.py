from __future__ import annotations

from asyncio import Future
from typing import Any, Callable, List, TypeVar

__all__ = ('apply_callback',)

T = TypeVar('T', str, List[str])


async def apply_callback(fut: Future[T], converter: Callable[[T], Any]) -> Any:
    result = await fut
    if result == b'QUEUED':
        return None
    else:
        return converter(result)
