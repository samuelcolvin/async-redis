from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, Union

from hiredis import hiredis

__all__ = ('open_connection', 'RedisStreamReader')

_DEFAULT_LIMIT = 2 ** 16  # 64 KiB


async def open_connection(
    host: str, port: int, *, limit: int = _DEFAULT_LIMIT, **kwds: Any
) -> Tuple['RedisStreamReader', asyncio.StreamWriter]:
    loop = asyncio.get_event_loop()
    reader = RedisStreamReader(limit=limit, loop=loop)
    protocol = asyncio.StreamReaderProtocol(reader, loop=loop)
    transport, _ = await loop.create_connection(lambda: protocol, host, port, **kwds)
    writer = asyncio.StreamWriter(transport, protocol, reader, loop)
    return reader, writer


class RedisStreamReader(asyncio.StreamReader):
    """
    Modified asyncio.StreamReader that uses a hiredis.Reader instead of bytearray as a buffer, otherwise
    this class attempts to keep the flow control logic unchanged
    """

    __slots__ = '_limit', '_loop', '_eof', '_waiter', '_exception', '_transport', '_paused', 'hi_reader'
    _source_traceback = None

    def __init__(self, limit: int, loop: asyncio.AbstractEventLoop):
        if limit <= 0:
            raise ValueError('Limit cannot be <= 0')

        self._limit = limit
        self._loop = loop
        self._eof: bool = False  # Whether we're done.
        self._waiter: Optional[asyncio.Future[None]] = None  # A future used by _wait_for_data()
        self._exception: Optional[Exception] = None
        self._transport: Optional[asyncio.Transport] = None
        self._paused: bool = False
        self.hi_reader = hiredis.Reader()

    def feed_data(self, data: bytes) -> None:
        assert not self._eof, 'feed_data after feed_eof'

        if not data:
            return

        self.hi_reader.feed(data)
        self._wakeup_waiter()

        if self._transport is not None and not self._paused and self.hi_reader.len() > 2 * self._limit:
            try:
                self._transport.pause_reading()
            except NotImplementedError:
                # The transport can't be paused.
                # We'll just have to buffer all data.
                # Forget the transport so we don't keep trying.
                self._transport = None
            else:
                self._paused = True

    async def read_redis(self) -> Union[bytes, List[bytes]]:
        """
        Return a parsed Redis object or an exception when something wrong happened.
        """
        if self._exception is not None:
            raise self._exception

        while True:
            obj = self.hi_reader.gets()

            if obj is not False:
                self._maybe_resume_transport()
                return obj

            if self._eof:
                self.hi_reader = hiredis.Reader()
                raise asyncio.IncompleteReadError(b'<redis>', None)

            await self._wait_for_data('read_redis')

    def _maybe_resume_transport(self) -> None:
        if self._paused and self.hi_reader.len() <= self._limit:
            self._paused = False
            self._transport.resume_reading()  # type: ignore

    # to satisfy mypy since the type hints for asyncio.StreamReader are wrong
    if TYPE_CHECKING:

        def _wakeup_waiter(self) -> None:
            ...

        async def _wait_for_data(self, func: str) -> None:
            ...
