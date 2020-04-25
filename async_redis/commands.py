from abc import ABC, abstractmethod
from typing import Coroutine, Any, Literal, Sequence, Tuple, List

from .typing import ArgType, CommandArgs, DecodeType

__all__ = ('AbstractCommands',)


class AbstractCommands(ABC):
    """
    String commands, see http://redis.io/commands/#string
    """

    @abstractmethod
    def execute(self, args: CommandArgs, *, decode: DecodeType = None, ok: bool = False) -> Coroutine[None, None, Any]:
        ...

    def append(self, key: ArgType, value: ArgType) -> Coroutine[None, None, int]:
        """
        Append a value to key.
        """
        return self.execute((b'APPEND', key, value), decode='int')

    def bitcount(self, key: ArgType, start: int = None, end: int = None) -> Coroutine[None, None, int]:
        """
        Count set bits in a string.

        :raises TypeError: if only start or end specified.
        """
        if start is not None and end is not None:
            args = (start, end)
        elif start is None and end is None:
            args = ()
        else:
            raise TypeError('both start and stop must be specified, or neither')
        return self.execute((b'BITCOUNT', key, *args), decode='int')

    # TODO bitfield

    def bitop(self, dest: ArgType, op: Literal['AND', 'OR', 'XOR', 'NOT'], key: ArgType, *keys: ArgType) -> Coroutine[None, None, None]:
        """
        Perform bitwise AND, OR, XOR or NOT operations between strings.
        """
        return self.execute((b'BITOP', op, dest, key, *keys), ok=True)

    def bitpos(self, key: ArgType, bit: Literal[0, 1], start: int = None, end: int = None) -> Coroutine[None, None, int]:
        """
        Find first bit set or clear in a string.

        :raises ValueError: if bit is not 0 or 1
        """
        if bit not in (1, 0):
            raise ValueError("bit argument must be either 1 or 0")
        bytes_range = []
        if start is not None:
            bytes_range.append(start)
        if end is not None:
            if start is None:
                bytes_range = [0, end]
            else:
                bytes_range.append(end)
        return self.execute((b'BITPOS', key, bit, *bytes_range), decode='int')

    def decr(self, key: ArgType) -> Coroutine[None, None, int]:
        """
        Decrement the integer value of a key by one.
        """
        return self.execute((b'DECR', key), decode='int')

    def decrby(self, key: ArgType, decrement: int) -> Coroutine[None, None, int]:
        """
        Decrement the integer value of a key by the given number.
        """
        return self.execute((b'DECRBY', key, decrement), decode='int')

    def get(self, key: ArgType, *, decode: bool = True) -> Coroutine[None, None, str]:
        """
        Get the value of a key.
        """
        return self.execute((b'GET', key), decode='str' if decode else None)

    def getbit(self, key: ArgType, offset: int) -> Coroutine[None, None, int]:
        """
        Returns the bit value at offset in the string value stored at key, offset must be an int greaterthan 0
        """
        return self.execute((b'GETBIT', key, offset), decode='int')

    def getrange(self, key: ArgType, start: int, end: int, *, decode: bool = True) -> Coroutine[None, None, str]:
        """
        Get a substring of the string stored at a key.
        """
        return self.execute((b'GETRANGE', key, start, end), decode='str' if decode else None)

    def getset(self, key: ArgType, value, *, decode: bool = True) -> Coroutine[None, None, str]:
        """
        Set the string value of a key and return its old value.
        """
        return self.execute((b'GETSET', key, value), decode='str' if decode else None)

    def incr(self, key: ArgType) -> Coroutine[None, None, int]:
        """
        Increment the integer value of a key by one.
        """
        return self.execute((b'INCR', key), decode='int')

    def incrby(self, key: ArgType, increment: int) -> Coroutine[None, None, int]:
        """
        Increment the integer value of a key by the given amount.
        """
        return self.execute((b'INCRBY', key, increment))

    def incrbyfloat(self, key: ArgType, increment: float) -> Coroutine[None, None, float]:
        """
        Increment the float value of a key by the given amount.
        """
        return self.execute((b'INCRBYFLOAT', key, increment), decode='float')

    def mget(self, key: ArgType, *keys, decode: bool = True) -> Coroutine[None, None, str]:
        """
        Get the values of all the given keys.
        """
        return self.execute((b'MGET', key, *keys), decode='str' if decode else None)

    def mset(self, *args: Sequence[Tuple[ArgType, ArgType]], **kwargs: ArgType) -> Coroutine[None, None, None]:
        """
        Set multiple keys to multiple values or unpack dict to keys & values.
        """
        command: List[ArgType] = [b'MSET']
        for k, v in args:
            command.extend([k, v])
        for k, v in kwargs.items():
            command.extend([k, v])

        return self.execute(command, ok=True)

    def msetnx(self, *args: Sequence[Tuple[ArgType, ArgType]], **kwargs: ArgType) -> Coroutine[None, None, int]:
        """
        Set multiple keys to multiple values, only if none of the keys exist.
        """
        command: List[ArgType] = [b'MSETNX']
        for k, v in args:
            command.extend([k, v])
        for k, v in kwargs.items():
            command.extend([k, v])

        return self.execute(command, decode='int')

    def psetex(self, key: ArgType, milliseconds: int, value: ArgType):
        """
        Set the value and expiration in milliseconds of a key.

        :raises TypeError: if milliseconds is not int
        """
        return self.execute((b'PSETEX', key, milliseconds, value), ok=True)

    def set(self, key: ArgType, value: ArgType, *, expire: int = None, pexpire: int = None, if_exists: bool = None, if_not_exists: bool = None) -> Coroutine[None, None, None]:
        """
        Set the string value of a key.
        """
        args = [b'SET', key, value]
        if expire:
            args.extend([b'EX', expire])
        if pexpire:
            args.extend([b'PX', pexpire])

        if if_exists:
            args.append(b'XX')
        elif if_not_exists:
            args.append(b'NX')
        return self.execute(args)

    # def setbit(self, key: ArgType, offset, value):
    #     """
    #     Sets or clears the bit at offset in the string value stored at key.
    #
    #     :raises TypeError: if offset is not int
    #     :raises ValueError: if offset is less than 0 or value is not 0 or 1
    #     """
    #     if not isinstance(offset, int):
    #         raise TypeError("offset argument must be int")
    #     if offset < 0:
    #         raise ValueError("offset must be greater equal 0")
    #     if value not in (0, 1):
    #         raise ValueError("value argument must be either 1 or 0")
    #     return self.execute((b'SETBIT', key, offset, value))
    #
    # def setex(self, key: ArgType, seconds, value):
    #     """
    #     Set the value and expiration of a key.
    #
    #     If seconds is float it will be multiplied by 1000
    #     coerced to int and passed to `psetex` method.
    #
    #     :raises TypeError: if seconds is neither int nor float
    #     """
    #     if isinstance(seconds, float):
    #         return self.psetex(key, int(seconds * 1000), value)
    #     if not isinstance(seconds, int):
    #         raise TypeError("milliseconds argument must be int")
    #     fut = self.execute((b'SETEX', key, seconds, value))
    #     return wait_ok(fut)
    #
    # def setnx(self, key: ArgType, value):
    #     """
    #     Set the value of a key, only if the key does not exist.
    #     """
    #     fut = self.execute((b'SETNX', key, value))
    #     return wait_convert(fut, bool)
    #
    # def setrange(self, key: ArgType, offset, value):
    #     """
    #     Overwrite part of a string at key starting at the specified offset.
    #
    #     :raises TypeError: if offset is not int
    #     :raises ValueError: if offset less than 0
    #     """
    #     if not isinstance(offset, int):
    #         raise TypeError("offset argument must be int")
    #     if offset < 0:
    #         raise ValueError("offset must be greater equal 0")
    #     return self.execute((b'SETRANGE', key, offset, value))
    #
    # def strlen(self, key: ArgType):
    #     """
    #     Get the length of the value stored in a key.
    #     """
    #     return self.execute((b'STRLEN', key))
