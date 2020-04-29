from __future__ import annotations

from asyncio import Lock, StreamWriter
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence

from hiredis import hiredis

from .streams import RedisStreamReader, open_connection
from .typing import CommandArgs, ResultType, ReturnAs

__all__ = 'ConnectionSettings', 'create_raw_connection', 'RawConnection'


@dataclass
class ConnectionSettings:
    """
    Connection settings
    """

    host: str = 'localhost'
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    encoding: str = 'utf8'

    def __repr__(self) -> str:
        # have to do it this way since asdict and __dict__ on dataclasses don't work with cython
        fields = 'host', 'port', 'database', 'password', 'encoding'
        return 'RedisSettings({})'.format(', '.join(f'{f}={getattr(self, f)!r}' for f in fields))


async def create_raw_connection(conn_settings: ConnectionSettings) -> 'RawConnection':
    """
    Connect to a redis database and create a new RawConnection.
    """
    reader, writer = await open_connection(conn_settings.host, conn_settings.port)
    return RawConnection(reader, writer, conn_settings.encoding)


default_ok_msg: bytes = b'OK'
return_as_lookup: Dict[str, Callable[[bytes], Any]] = {
    'int': int,
    'float': float,
    'bool': bool,
}


class RawConnection:
    """
    Low level interface to write to and read from redis.

    You probably don't want to use this directly
    """

    __slots__ = '_reader', '_writer', '_encoding', '_hi_raw', '_hi_enc', '_lock', '_expected_ok_msg'

    def __init__(self, reader: RedisStreamReader, writer: StreamWriter, encoding: str):
        self._reader = reader
        self._writer = writer
        self._encoding = encoding
        self._lock = Lock()
        self._hi_raw = reader.hi_reader
        self._hi_enc = hiredis.Reader(encoding=encoding)
        self._expected_ok_msg: bytes = default_ok_msg

    async def execute(self, args: CommandArgs, return_as: ReturnAs = None) -> ResultType:
        buf = bytearray()
        self._encode_command(buf, args)
        self._set_reader_encoding(return_as)
        async with self._lock:
            self._writer.write(buf)
            del buf
            await self._writer.drain()
            return await self._read_result(return_as)

    async def execute_many(self, commands: Sequence[CommandArgs], return_as: ReturnAs = None) -> List[ResultType]:
        # TODO need tuples of command and return_as
        buf = bytearray()
        for args in commands:
            self._encode_command(buf, args)
        self._set_reader_encoding(None)
        async with self._lock:
            self._writer.write(buf)
            del buf
            await self._writer.drain()
            # TODO need to raise an error but read all answers first
            return [await self._read_result(return_as) for _ in range(len(commands))]

    async def close(self) -> None:
        async with self._lock:
            self._writer.close()
            await self._writer.wait_closed()

    def set_ok_msg(self, msg: bytes = default_ok_msg) -> None:
        self._expected_ok_msg = msg

    def _set_reader_encoding(self, return_as: ReturnAs) -> None:
        self._reader.hi_reader = self._hi_enc if return_as == 'str' else self._hi_raw

    async def _read_result(self, return_as: ReturnAs) -> ResultType:
        result = await self._reader.read_redis()

        if return_as in (None, 'str'):
            return result
        elif return_as == 'ok':
            if result != self._expected_ok_msg:
                # TODO this needs to be deferred for execute_many
                raise RuntimeError(f'unexpected result {result!r}')
            return None

        func = return_as_lookup[return_as]  # type: ignore
        if isinstance(result, bytes):
            return func(result)
        else:
            # result must be a list
            return [func(r) for r in result]

    def _to_str(self, b: bytes) -> str:
        # TODO might be possible to change this once https://github.com/redis/hiredis-py/pull/96 gets released
        return b.decode(self._encoding)

    def _encode_command(self, buf: bytearray, args: CommandArgs) -> None:
        """
        Encodes arguments into redis bulk-strings array.

        Raises TypeError if any arg is not a bytes, bytearray, str, int, or float.
        """
        buf.extend(b'*%d\r\n' % len(args))

        for arg in args:
            if isinstance(arg, bytes):
                bin_arg = arg
            elif isinstance(arg, str):
                bin_arg = arg.encode(self._encoding)
            elif isinstance(arg, int):
                bin_arg = b'%d' % arg
            elif isinstance(arg, float):
                bin_arg = f'{arg}'.encode('ascii')
            elif isinstance(arg, bytearray):
                bin_arg = bytes(arg)
            else:
                raise TypeError(
                    f"Invalid argument: '{arg!r}' {arg.__class__} expected bytes, bytearray, str, int, or float"
                )
            buf.extend(b'$%d\r\n%s\r\n' % (len(bin_arg), bin_arg))
