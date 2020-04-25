from asyncio import open_connection, StreamReader, StreamWriter
from dataclasses import dataclass
from typing import Union, Sequence, List, Optional

import hiredis

from .typing import CommandArgs, DecodeType, ResultType

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


class RawConnection:
    """
    Low level interface to write to and read from redis.

    You probably don't want to use this directly
    """
    __slots__ = '_reader', '_writer', '_encoding', '_hi_raw', '_hi_enc'

    def __init__(self, reader: StreamReader, writer: StreamWriter, encoding: str):
        self._reader = reader
        self._writer = writer
        self._encoding = encoding
        self._hi_raw = hiredis.Reader()
        self._hi_enc = hiredis.Reader(encoding=encoding)

    async def execute(self, args: CommandArgs, *, decode_mode: DecodeType = None) -> ResultType:
        buf = bytearray()
        self._encode_command(buf, args)
        self._writer.write(buf)
        await self._writer.drain()
        return await self._read_result(decode_mode)

    async def execute_many(self, commands: Sequence[CommandArgs]) -> List[ResultType]:
        buf = bytearray()
        for args in commands:
            self._encode_command(buf, args)
        self._writer.write(buf)
        await self._writer.drain()
        return [await self._read_result(None) for _ in range(len(commands))]

    async def close(self):
        self._writer.close()
        await self._writer.wait_closed()

    async def _read_result(self, decode_mode: DecodeType) -> ResultType:
        hi = self._hi_enc if decode_mode == 'str' else self._hi_raw
        result = False
        while result is False:
            raw_line = await self._reader.readline()
            hi.feed(raw_line)
            result = hi.gets()
        if decode_mode == 'int':
            if result.__class__ == bytes:
                return int(result)
            else:
                return [int(r) for r in result]
        elif decode_mode == 'float':
            if result.__class__ == bytes:
                return float(result)
            else:
                return [float(r) for r in result]
        else:
            return result

    def _encode_command(self, buf: bytearray, args: CommandArgs) -> None:
        """
        Encodes arguments into redis bulk-strings array.

        Raises TypeError if any arg is not a bytearray, bytes, str, float, or int.
        """
        buf.extend(b'*%d\r\n' % len(args))

        for arg in args:
            cls = arg.__class__
            if cls == bytes or cls == bytearray:
                bin_arg: Union[bytes, bytearray] = arg
            elif cls == str:
                bin_arg = arg.encode(self._encoding)
            elif cls == int or cls == float:
                bin_arg = b'%r' % arg
            else:
                raise TypeError(f'Argument {arg!r} expected to be a bytearray, bytes, str, float, or int')
            buf.extend(b'$%d\r\n%s\r\n' % (len(bin_arg), bin_arg))
