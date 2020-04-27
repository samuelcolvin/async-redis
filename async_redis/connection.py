from asyncio import Lock, StreamReader, StreamWriter, open_connection
from dataclasses import dataclass
from typing import List, Optional, Sequence, Union

import hiredis

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
        return 'RedisSettings({})'.format(', '.join(f'{k}={v!r}' for k, v in self.__dict__.items()))


async def create_raw_connection(conn_settings: ConnectionSettings) -> 'RawConnection':
    """
    Connect to a redis database and create a new RawConnection.
    """
    reader, writer = await open_connection(conn_settings.host, conn_settings.port)
    return RawConnection(reader, writer, conn_settings.encoding)


return_as_lookup = {'int': int, 'float': float, 'bool': bool}


class RawConnection:
    """
    Low level interface to write to and read from redis.

    You probably don't want to use this directly
    """

    __slots__ = '_reader', '_writer', '_encoding', '_hi_raw', '_hi_enc', '_lock'

    def __init__(self, reader: StreamReader, writer: StreamWriter, encoding: str):
        self._reader = reader
        self._writer = writer
        self._encoding = encoding
        self._hi_raw = hiredis.Reader()
        self._hi_enc = hiredis.Reader(encoding=encoding)
        self._lock = Lock()

    async def execute(self, args: CommandArgs, return_as: ReturnAs = None) -> ResultType:
        async with self._lock:
            buf = bytearray()
            self._encode_command(buf, args)
            self._writer.write(buf)
            await self._writer.drain()
            # TODO need a way to check for OK and raise an error if not
            return await self._read_result(return_as)

    async def execute_many(self, commands: Sequence[CommandArgs], return_as: ReturnAs = None) -> List[ResultType]:
        # TODO need tuples of command and return_as
        async with self._lock:
            buf = bytearray()
            for args in commands:
                self._encode_command(buf, args)
            self._writer.write(buf)
            await self._writer.drain()
            # TODO need to raise an error but read all answers first
            return [await self._read_result(return_as) for _ in range(len(commands))]

    async def close(self) -> None:
        async with self._lock:
            self._writer.close()
            await self._writer.wait_closed()

    async def _read_result(self, return_as: ReturnAs) -> ResultType:
        hi = self._hi_enc if return_as == 'str' else self._hi_raw
        result = False
        while result is False:
            raw_line = await self._reader.readline()
            hi.feed(raw_line)
            result = hi.gets()

        if return_as is None:
            return result

        try:
            func = return_as_lookup[return_as]
        except KeyError:
            return result
        else:
            if result.__class__ == bytes:
                return func(result)
            else:
                # result must be a list
                return [func(r) for r in result]  # type: ignore

    def _encode_command(self, buf: bytearray, args: CommandArgs) -> None:
        """
        Encodes arguments into redis bulk-strings array.

        Raises TypeError if any arg is not a bytearray, bytes, str, float, or int.
        """
        buf.extend(b'*%d\r\n' % len(args))

        for arg in args:
            cls = arg.__class__
            if cls in (bytes, bytearray):
                bin_arg: Union[bytes, bytearray] = arg  # type: ignore
            elif cls == str:
                bin_arg = arg.encode(self._encoding)  # type: ignore
            elif cls in (int, float):
                bin_arg = b'%r' % arg
            else:
                raise TypeError(
                    f"Invalid argument: '{arg!r}' {arg.__class__} expected bytearray, bytes, str, float, or int"
                )
            buf.extend(b'$%d\r\n%s\r\n' % (len(bin_arg), bin_arg))
