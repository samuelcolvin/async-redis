import asyncio
from typing import Optional, Union

import hiredis


ArgTypes = Union[bytes, bytearray, str, int, float]


async def connect(host: str = 'localhost', port: int = 6379) -> 'RawConnection':
    reader, writer = await asyncio.open_connection(host, port)
    return RawConnection(reader, writer)


class RawConnection:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self._reader = reader
        self._writer = writer

    async def execute(self, command: bytes, *args: ArgTypes):
        self._writer.write(encode_command(command, *args))
        await self._writer.drain()
        reader = hiredis.Reader()
        result = False
        while result is False:
            raw_line = await self._reader.readline()
            reader.feed(raw_line)
            result = reader.gets()
        return result

    async def close(self):
        self._writer.close()
        await self._writer.wait_closed()


def encode_command(*args: ArgTypes, buf: Optional[bytearray] = None) -> bytearray:
    """
    Encodes arguments into redis bulk-strings array.

    Raises TypeError if any of args are not bytearray, bytes, str, float, or int.
    """
    if buf is None:
        buf = bytearray()
    buf.extend(b'*%d\r\n' % len(args))

    for arg in args:
        cls = arg.__class__
        if cls == bytes or cls == bytearray:
            bin_arg: Union[bytes, bytearray] = arg
        elif cls == str:
            bin_arg = arg.encode()
        elif cls == int or cls == float:
            bin_arg = b'%d' % arg
        else:
            raise TypeError(f'Argument {arg!r} expected to be of bytearray, bytes, float, int, or str type')
        buf.extend(b'$%d\r\n%s\r\n' % (len(bin_arg), bin_arg))
    return buf
