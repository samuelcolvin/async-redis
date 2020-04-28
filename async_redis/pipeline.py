from __future__ import annotations

from types import TracebackType
from typing import Optional, Type

from .connection import RawConnection
from .pipeline_commands import CommandsPipeline

__all__ = ('PipelineContext',)


class PipelineContext:
    def __init__(self, raw_connection: RawConnection) -> None:
        self._conn = raw_connection
        self._pipeline: Optional[CommandsPipeline] = None

    async def __aenter__(self) -> CommandsPipeline:
        self._pipeline = CommandsPipeline(self._conn)
        return self._pipeline

    async def __aexit__(
        self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Optional[TracebackType]
    ) -> None:
        if exc_type:
            self._pipeline = None
        elif self._pipeline is not None:
            await self._pipeline.execute()
