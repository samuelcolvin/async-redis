from __future__ import annotations

from typing import List

from .commands import AbstractCommands
from .connection import RawConnection
from .typing import CommandArgs, ResultType, ReturnAs

__all__ = ('CommandsPipeline',)


class CommandsPipeline(AbstractCommands):
    def __init__(self, raw_connection: RawConnection) -> None:
        self._conn = raw_connection
        self._pipeline: List[CommandArgs] = []

    def _execute(self, args: CommandArgs, return_as: ReturnAs) -> None:
        self._pipeline.append(args)

    async def execute(self, return_as: ReturnAs = None) -> List[ResultType]:
        r: List[ResultType] = []
        if self._pipeline:
            r = await self._conn.execute_many(self._pipeline, return_as)
            self._pipeline = []
        return r
