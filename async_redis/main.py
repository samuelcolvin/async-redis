from __future__ import annotations

import asyncio
from types import TracebackType
from typing import Any, Generator, Optional, Type

from .commands import AbstractCommands
from .connection import ConnectionSettings, RawConnection, create_raw_connection
from .pipeline import PipelineContext
from .typing import CommandArgs, ResultType, ReturnAs

__all__ = 'Redis', 'connect'


class Redis(AbstractCommands):
    __slots__ = ('_conn',)

    def __init__(self, raw_connection: RawConnection):
        self._conn = raw_connection

    async def _execute(self, args: CommandArgs, return_as: ReturnAs) -> ResultType:
        # TODO probably need to shield self._conn.execute to avoid reading part of an answer
        return await self._conn.execute(args, return_as=return_as)

    def pipeline(self) -> PipelineContext:
        return PipelineContext(self._conn)

    async def close(self) -> None:
        await self._conn.close()


def connect(
    connection_settings: Optional[ConnectionSettings] = None,
    *,
    host: str = None,
    port: int = None,
    database: int = None,
) -> 'RedisConnector':
    if connection_settings:
        conn_settings = connection_settings
    else:
        kwargs = dict(host=host, port=port, database=database)
        conn_settings = ConnectionSettings(**{k: v for k, v in kwargs.items() if v is not None})  # type: ignore

    return RedisConnector(conn_settings)


class RedisConnector:
    """
    Simple shim to allow both "await async_redis.connect(...)" and "async with async_redis.connect(...)" to work
    """

    def __init__(self, conn_settings: ConnectionSettings):
        self.conn_settings = conn_settings
        self.redis: Optional[Redis] = None
        self.lock = asyncio.Lock()

    async def open(self) -> Redis:
        async with self.lock:
            if self.redis is None:
                conn = await create_raw_connection(self.conn_settings)
                self.redis = Redis(conn)
        return self.redis

    def __await__(self) -> Generator[Any, None, Redis]:
        return self.open().__await__()

    async def __aenter__(self) -> Redis:
        return await self.open()

    async def __aexit__(
        self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Optional[TracebackType]
    ) -> None:
        async with self.lock:
            if self.redis is not None:
                await self.redis.close()
                self.redis = None
