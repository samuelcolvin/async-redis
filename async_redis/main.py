import asyncio
from typing import Any, Generator, Optional

from .commands import AbstractCommands
from .connection import ConnectionSettings, RawConnection, create_raw_connection
from .typing import CommandArgs, Decoders

__all__ = 'Redis', 'connect'


class Redis(AbstractCommands):
    def __init__(self, raw_connection: RawConnection):
        self._conn = raw_connection

    async def execute(self, args: CommandArgs, decoder: Decoders) -> Any:
        r = await self._conn.execute(args, decoder=decoder)
        if decoder == Decoders.ok:
            if r != b'OK':
                raise RuntimeError(f'unexpected result {r!r}')
            return None
        else:
            return r

    async def close(self) -> None:
        await self._conn.close()


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

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async with self.lock:
            if self.redis is not None:
                await self.redis.close()
                self.redis = None


def connect(
    connection_settings: Optional[ConnectionSettings] = None,
    *,
    host: str = None,
    port: int = None,
    database: int = None,
) -> RedisConnector:
    if connection_settings:
        conn_settings = connection_settings
    else:
        kwargs = dict(host=host, port=port, database=database)
        conn_settings = ConnectionSettings(**{k: v for k, v in kwargs.items() if v is not None})

    return RedisConnector(conn_settings)
