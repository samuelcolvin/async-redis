from abc import abstractmethod
from typing import Any, Coroutine, List, Tuple, TypeVar, Union

from .typing import ArgType, CommandArgs, Decoders, Literal

__all__ = ('AbstractCommands',)

T = TypeVar('T', bytes, str, int, float, 'None')
Result = Coroutine[Any, Any, T]


class AbstractCommands:
    @abstractmethod
    def execute(self, args: CommandArgs, decoder: Decoders) -> Any:
        ...

    """
    String commands, see http://redis.io/commands/#string
    """

    def append(self, key: ArgType, value: ArgType) -> Result[int]:
        """
        Append a value to key.
        """
        return self.execute((b'APPEND', key, value), Decoders.int)

    def bitcount(self, key: ArgType, start: int = None, end: int = None) -> Result[int]:
        """
        Count set bits in a string.
        """
        command = [b'BITCOUNT', key]
        if start is not None and end is not None:
            command.extend([start, end])
        elif not (start is None and end is None):
            raise TypeError('both start and stop must be specified, or neither')
        return self.execute(command, Decoders.int)

    # TODO bitfield

    def bitop(
        self, dest: ArgType, op: Literal['AND', 'OR', 'XOR', 'NOT'], key: ArgType, *keys: ArgType
    ) -> Result[None]:
        """
        Perform bitwise AND, OR, XOR or NOT operations between strings.
        """
        return self.execute((b'BITOP', op, dest, key, *keys), Decoders.ok)

    def bitpos(self, key: ArgType, bit: Literal[0, 1], start: int = None, end: int = None) -> Result[int]:
        """
        Find first bit set or clear in a string.
        """
        command: List[ArgType] = [b'BITPOS', key, bit]
        if start is not None:
            command.append(start)
            if end is not None:
                command.append(end)
        elif end is not None:
            command.extend([0, end])
        return self.execute(command, Decoders.int)

    def decr(self, key: ArgType) -> Result[int]:
        """
        Decrement the integer value of a key by one.
        """
        return self.execute((b'DECR', key), Decoders.int)

    def decrby(self, key: ArgType, decrement: int) -> Result[int]:
        """
        Decrement the integer value of a key by the given number.
        """
        return self.execute((b'DECRBY', key, decrement), Decoders.int)

    def get(self, key: ArgType, *, decode: bool = True) -> Result[str]:
        """
        Get the value of a key.
        """
        return self.execute((b'GET', key), Decoders.str if decode else Decoders.bytes)

    def getbit(self, key: ArgType, offset: int) -> Result[int]:
        """
        Returns the bit value at offset in the string value stored at key, offset must be an int greater than 0
        """
        return self.execute((b'GETBIT', key, offset), Decoders.int)

    def getrange(self, key: ArgType, start: int, end: int, *, decode: bool = True) -> Result[str]:
        """
        Get a substring of the string stored at a key.
        """
        return self.execute((b'GETRANGE', key, start, end), Decoders.str if decode else Decoders.bytes)

    def getset(self, key: ArgType, value: ArgType, *, decode: bool = True) -> Result[str]:
        """
        Set the string value of a key and return its old value.
        """
        return self.execute((b'GETSET', key, value), Decoders.str if decode else Decoders.bytes)

    def incr(self, key: ArgType) -> Result[int]:
        """
        Increment the integer value of a key by one.
        """
        return self.execute((b'INCR', key), Decoders.int)

    def incrby(self, key: ArgType, increment: int) -> Result[int]:
        """
        Increment the integer value of a key by the given amount.
        """
        return self.execute((b'INCRBY', key, increment), Decoders.int)

    def incrbyfloat(self, key: ArgType, increment: float) -> Result[float]:
        """
        Increment the float value of a key by the given amount.
        """
        return self.execute((b'INCRBYFLOAT', key, increment), Decoders.float)

    def mget(self, key: ArgType, *keys: ArgType, decode: bool = True) -> Result[str]:
        """
        Get the values of all the given keys.
        """
        return self.execute((b'MGET', key, *keys), Decoders.str if decode else Decoders.bytes)

    def mset(self, *args: Tuple[ArgType, ArgType], **kwargs: ArgType) -> Result[None]:
        """
        Set multiple keys to multiple values or unpack dict to keys & values.
        """
        command: List[ArgType] = [b'MSET']
        for k1, v1 in args:
            command.extend([k1, v1])
        for k2, v2 in kwargs.items():
            command.extend([k2, v2])

        return self.execute(command, Decoders.ok)

    def msetnx(self, *args: Tuple[ArgType, ArgType], **kwargs: ArgType) -> Result[int]:
        """
        Set multiple keys to multiple values, only if none of the keys exist.
        """
        command: List[ArgType] = [b'MSETNX']
        for k1, v1 in args:
            command.extend([k1, v1])
        for k2, v2 in kwargs.items():
            command.extend([k2, v2])

        return self.execute(command, Decoders.int)

    def psetex(self, key: ArgType, milliseconds: int, value: ArgType) -> Result[None]:
        """
        Set the value and expiration in milliseconds of a key.
        """
        return self.execute((b'PSETEX', key, milliseconds, value), Decoders.ok)

    def set(
        self,
        key: ArgType,
        value: ArgType,
        *,
        expire: int = None,
        pexpire: int = None,
        if_exists: bool = None,
        if_not_exists: bool = None,
    ) -> Result[None]:
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
        return self.execute(args, Decoders.ok)

    def setbit(self, key: ArgType, offset: int, value: Literal[0, 1]) -> Result[Literal[0, 1]]:
        """
        Sets or clears the bit at offset in the string value stored at key.
        """
        return self.execute((b'SETBIT', key, offset, value), Decoders.int)

    def setex(self, key: ArgType, seconds: Union[int, float], value: ArgType) -> Result[None]:
        """
        Set the value and expiration of a key.

        If seconds is float it will be multiplied by 1000 coerced to int and passed to `psetex` method.
        """
        if isinstance(seconds, float):
            return self.psetex(key, int(seconds * 1000), value)
        else:
            return self.execute((b'SETEX', key, seconds, value), Decoders.ok)

    def setnx(self, key: ArgType, value: ArgType) -> Result[bool]:
        """
        Set the value of a key, only if the key does not exist.
        """
        return self.execute((b'SETNX', key, value), Decoders.bool)

    def setrange(self, key: ArgType, offset: int, value: ArgType) -> Result[int]:
        """
        Overwrite part of a string at key starting at the specified offset.
        """
        return self.execute((b'SETRANGE', key, offset, value), Decoders.int)

    # TODO stralgo

    def strlen(self, key: ArgType) -> Result[int]:
        """
        Get the length of the value stored in a key.
        """
        return self.execute((b'STRLEN', key), Decoders.int)
