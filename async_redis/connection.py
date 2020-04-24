from asyncio import open_connection, StreamReader, StreamWriter
from typing import Union, Tuple, Sequence, List

import hiredis


ArgTypes = Union[bytes, bytearray, str, int, float]
CommandArgs = Tuple[ArgTypes, ...]


async def connect(host: str = 'localhost', port: int = 6379) -> 'RawConnection':
    """
    Connect to a redis database and create a new RawConnection.
    """
    reader, writer = await open_connection(host, port)
    return RawConnection(reader, writer)


class RawConnection:
    """
    Low level interface to write to and read from redis.

    You probably don't want to use this directly
    """
    __slots__ = '_reader', '_writer'

    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self._reader = reader
        self._writer = writer

    async def execute(self, args: CommandArgs) -> bytes:
        buf = bytearray()
        encode_command(buf, args)
        self._writer.write(buf)
        await self._writer.drain()
        return await self._read_result()

    async def execute_many(self, commands: Sequence[CommandArgs]) -> List[bytes]:
        buf = bytearray()
        for args in commands:
            encode_command(buf, args)
        self._writer.write(buf)
        await self._writer.drain()
        return [await self._read_result() for _ in range(len(commands))]

    async def close(self):
        self._writer.close()
        await self._writer.wait_closed()

    async def _read_result(self):
        reader = hiredis.Reader()
        result = False
        while result is False:
            raw_line = await self._reader.readline()
            reader.feed(raw_line)
            result = reader.gets()
        return result


def encode_command(buf: bytearray, args: CommandArgs) -> None:
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
            bin_arg = arg.encode()
        elif cls == int or cls == float:
            bin_arg = b'%r' % arg
        else:
            raise TypeError(f'Argument {arg!r} expected to be a bytearray, bytes, str, float, or int')
        buf.extend(b'$%d\r\n%s\r\n' % (len(bin_arg), bin_arg))
