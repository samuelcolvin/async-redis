from __future__ import annotations

from abc import abstractmethod
from typing import Any, Coroutine, List, Tuple, TypeVar, Union

from .typing import ArgType, CommandArgs, Literal, ReturnAs

__all__ = ('AbstractCommands',)

T = TypeVar('T', bytes, str, int, float, 'None')
Result = Coroutine[Any, Any, T]


class AbstractCommands:
    @abstractmethod
    def _execute(self, args: CommandArgs, return_as: ReturnAs) -> Any:
        ...

    """
    String commands, see http://redis.io/commands/#string
    """

    def append(self, key: ArgType, value: ArgType) -> Result[int]:
        """
        Append a value to key.
        """
        return self._execute((b'APPEND', key, value), 'int')

    def bitcount(self, key: ArgType, start: int = None, end: int = None) -> Result[int]:
        """
        Count set bits in a string.
        """
        command = [b'BITCOUNT', key]
        if start is not None and end is not None:
            command.extend([start, end])
        elif not (start is None and end is None):
            raise TypeError('both start and stop must be specified, or neither')
        return self._execute(command, 'int')

    # TODO bitfield

    def bitop(
        self, dest: ArgType, op: Literal['AND', 'OR', 'XOR', 'NOT'], key: ArgType, *keys: ArgType
    ) -> Result[None]:
        """
        Perform bitwise AND, OR, XOR or NOT operations between strings.
        """
        return self._execute((b'BITOP', op, dest, key, *keys), 'ok')

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
        return self._execute(command, 'int')

    def decr(self, key: ArgType) -> Result[int]:
        """
        Decrement the integer value of a key by one.
        """
        return self._execute((b'DECR', key), 'int')

    def decrby(self, key: ArgType, decrement: int) -> Result[int]:
        """
        Decrement the integer value of a key by the given number.
        """
        return self._execute((b'DECRBY', key, decrement), 'int')

    def get(self, key: ArgType, *, decode: bool = True) -> Result[str]:
        """
        Get the value of a key.
        """
        return self._execute((b'GET', key), 'str' if decode else None)

    def getbit(self, key: ArgType, offset: int) -> Result[int]:
        """
        Returns the bit value at offset in the string value stored at key, offset must be an int greater than 0
        """
        return self._execute((b'GETBIT', key, offset), 'int')

    def getrange(self, key: ArgType, start: int, end: int, *, decode: bool = True) -> Result[str]:
        """
        Get a substring of the string stored at a key.
        """
        return self._execute((b'GETRANGE', key, start, end), 'str' if decode else None)

    def getset(self, key: ArgType, value: ArgType, *, decode: bool = True) -> Result[str]:
        """
        Set the string value of a key and return its old value.
        """
        return self._execute((b'GETSET', key, value), 'str' if decode else None)

    def incr(self, key: ArgType) -> Result[int]:
        """
        Increment the integer value of a key by one.
        """
        return self._execute((b'INCR', key), 'int')

    def incrby(self, key: ArgType, increment: int) -> Result[int]:
        """
        Increment the integer value of a key by the given amount.
        """
        return self._execute((b'INCRBY', key, increment), 'int')

    def incrbyfloat(self, key: ArgType, increment: float) -> Result[float]:
        """
        Increment the float value of a key by the given amount.
        """
        return self._execute((b'INCRBYFLOAT', key, increment), 'float')

    def mget(self, key: ArgType, *keys: ArgType, decode: bool = True) -> Result[str]:
        """
        Get the values of all the given keys.
        """
        return self._execute((b'MGET', key, *keys), 'str' if decode else None)

    def mset(self, *args: Tuple[ArgType, ArgType], **kwargs: ArgType) -> Result[None]:
        """
        Set multiple keys to multiple values or unpack dict to keys & values.
        """
        command: List[ArgType] = [b'MSET']
        for k1, v1 in args:
            command.extend([k1, v1])
        for k2, v2 in kwargs.items():
            command.extend([k2, v2])

        return self._execute(command, 'ok')

    def msetnx(self, *args: Tuple[ArgType, ArgType], **kwargs: ArgType) -> Result[int]:
        """
        Set multiple keys to multiple values, only if none of the keys exist.
        """
        command: List[ArgType] = [b'MSETNX']
        for k1, v1 in args:
            command.extend([k1, v1])
        for k2, v2 in kwargs.items():
            command.extend([k2, v2])

        return self._execute(command, 'int')

    def psetex(self, key: ArgType, milliseconds: int, value: ArgType) -> Result[None]:
        """
        Set the value and expiration in milliseconds of a key.
        """
        return self._execute((b'PSETEX', key, milliseconds, value), 'ok')

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
        return self._execute(args, 'ok')

    def setbit(self, key: ArgType, offset: int, value: Literal[0, 1]) -> Result[Literal[0, 1]]:
        """
        Sets or clears the bit at offset in the string value stored at key.
        """
        return self._execute((b'SETBIT', key, offset, value), 'int')

    def setex(self, key: ArgType, seconds: Union[int, float], value: ArgType) -> Result[None]:
        """
        Set the value and expiration of a key.

        If seconds is float it will be multiplied by 1000 coerced to int and passed to `psetex` method.
        """
        if isinstance(seconds, float):
            return self.psetex(key, int(seconds * 1000), value)
        else:
            return self._execute((b'SETEX', key, seconds, value), 'ok')

    def setnx(self, key: ArgType, value: ArgType) -> Result[bool]:
        """
        Set the value of a key, only if the key does not exist.
        """
        return self._execute((b'SETNX', key, value), 'bool')

    def setrange(self, key: ArgType, offset: int, value: ArgType) -> Result[int]:
        """
        Overwrite part of a string at key starting at the specified offset.
        """
        return self._execute((b'SETRANGE', key, offset, value), 'int')

    # TODO stralgo

    def strlen(self, key: ArgType) -> Result[int]:
        """
        Get the length of the value stored in a key.
        """
        return self._execute((b'STRLEN', key), 'int')
