from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any, Coroutine, Dict, List, Optional, Tuple, TypeVar, Union

from .typing import ArgType, CommandArgs, Literal, ReturnAs
from .utils import apply_callback

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

    """
    For commands, see http://redis.io/commands/#server
    """

    def bgrewriteaof(self) -> Result[None]:
        """
        Asynchronously rewrite the append-only file.
        """
        return self._execute((b'BGREWRITEAOF',), 'ok')

    def bgsave(self) -> Result[None]:
        """
        Asynchronously save the dataset to disk.
        """
        return self._execute((b'BGSAVE',), 'ok')

    def client_kill(self, *args: ArgType) -> Result[None]:
        """
        Kill the connection of a client.
        """
        return self._execute((b'CLIENT KILL', *args), 'ok')

    def client_list(self) -> Result[str]:
        """
        Get the list of client connections.

        Returns list of ClientInfo named tuples.
        """
        return self._execute((b'CLIENT', b'LIST'), 'str')

    def client_getname(self) -> Result[str]:
        """
        Get the current connection name.
        """
        return self._execute((b'CLIENT', b'GETNAME'), 'str')

    def client_pause(self, timeout: int) -> Result[int]:
        """
        Stop processing commands from clients for *timeout* milliseconds.
        """
        return self._execute((b'CLIENT', b'PAUSE', timeout), 'ok')

    def client_reply(self, set: Literal['ON', 'OFF', 'SKIP']) -> Result[None]:
        """
        Instruct the server whether to reply to commands
        """
        return self._execute((b'CLIENT', b'REPLY', set), 'ok')

    def client_setname(self, name: ArgType) -> Result[None]:
        """
        Set the current connection name.
        """
        return self._execute((b'CLIENT', b'SETNAME', name), 'ok')

    def command(self) -> Result[List[List[Union[int, str]]]]:
        """
        Get array of Redis commands.
        """
        return self._execute([b'COMMAND'], 'str')

    def command_count(self) -> Result[int]:
        """
        Get total number of Redis commands.
        """
        return self._execute((b'COMMAND', b'COUNT'), 'int')

    def command_getkeys(self, command: ArgType, *args: ArgType) -> Result[List[str]]:
        """
        Extract keys given a full Redis command.
        """
        return self._execute((b'COMMAND', b'GETKEYS', command, *args), 'str')

    def command_info(self, command: ArgType, *commands: ArgType) -> Result[List[List[Union[int, str]]]]:
        """
        Get array of specific Redis command details.
        """
        return self._execute((b'COMMAND', b'INFO', command, *commands), 'str')

    def config_get(self, parameter: Union[str, bytes] = '*') -> Result[Dict[str, str]]:
        """
        Get the value of a configuration parameter(s).

        If called without argument will return all parameters.
        """
        return apply_callback(self._execute((b'CONFIG', b'GET', parameter), 'str'), self._config_as_dict)

    @staticmethod
    def _config_as_dict(v: List[str]) -> Dict[str, str]:
        it = iter(v)
        return dict(zip(it, it))

    def config_rewrite(self) -> Result[None]:
        """
        Rewrite the configuration file with the in memory configuration.
        """
        return self._execute((b'CONFIG', b'REWRITE'), 'ok')

    def config_set(self, parameter: Union[str, bytes], value: ArgType) -> Result[None]:
        """
        Set a configuration parameter to the given value.
        """
        return self._execute((b'CONFIG', b'SET', parameter, value), 'ok')

    def config_resetstat(self) -> Result[None]:
        """
        Reset the stats returned by INFO.
        """
        return self._execute((b'CONFIG', b'RESETSTAT',), 'ok')

    def dbsize(self) -> Result[int]:
        """
        Return the number of keys in the selected database.
        """
        return self._execute((b'DBSIZE',), 'int')

    def debug_sleep(self, timeout: int) -> Result[None]:
        """
        Suspend connection for timeout seconds.
        """
        return self._execute((b'DEBUG', b'SLEEP', timeout), 'ok')

    def debug_object(self, key: ArgType) -> Result[str]:
        """
        Get debugging information about a key.
        """
        return self._execute((b'DEBUG', b'OBJECT', key), 'str')

    def debug_segfault(self) -> Result[bytes]:
        """
        Make the server crash.
        """
        return self._execute((b'DEBUG', b'SEGFAULT'), None)

    def flushall(self, async_: bool = False) -> Result[None]:
        """
        Remove all keys from all databases.

        :param async_: lets the entire dataset be freed asynchronously. Defaults False
        """
        if async_:
            return self._execute((b'FLUSHALL', b'ASYNC'), 'ok')
        else:
            return self._execute((b'FLUSHALL',), 'ok')

    def flushdb(self, async_: bool = False) -> Result[None]:
        """
        Remove all keys from the current database.

        :param async_: lets a single database be freed asynchronously. Defaults False
        """
        if async_:
            return self._execute((b'FLUSHDB', b'ASYNC'), 'ok')
        else:
            return self._execute((b'FLUSHDB',), 'ok')

    def info(
        self,
        section: Literal[
            'all',
            'default',
            'server',
            'clients',
            'memory',
            'persistence',
            'stats',
            'replication',
            'cpu',
            'commandstats',
            'cluster',
            'keyspace',
        ] = 'default',
    ) -> Result[Dict[str, Dict[str, str]]]:
        """
        Get information and statistics about the server.

        If called without argument will return default set of sections.
        """
        return apply_callback(self._execute((b'INFO', section), 'str'), self._parse_info)

    @staticmethod
    def _parse_info(info: str) -> Dict[str, Any]:
        res: Dict[str, Any] = {}
        for block in info.split('\r\n\r\n'):
            section, *extra = block.strip().splitlines()
            section = section[2:].lower()
            res[section] = tmp = {}
            for line in extra:
                value: Union[str, Dict[str, str]]
                key, value = line.split(':', 1)
                if ',' in line and '=' in line:
                    value = dict(i.split('=', 1) for i in value.split(','))  # type: ignore
                tmp[key] = value
        return res

    def lastsave(self) -> Result[None]:
        """
        Get the UNIX time stamp of the last successful save to disk.
        """
        return self._execute((b'LASTSAVE',), None)

    # TODO monitor

    def role(self) -> Result[bytes]:
        """
        Return the role of the server instance.

        Returns named tuples describing role of the instance.
        For fields information see http://redis.io/commands/role#output-format
        """
        return self._execute((b'ROLE',), 'str')

    def save(self) -> Result[None]:
        """
        Synchronously save the dataset to disk.
        """
        return self._execute((b'SAVE',), 'ok')

    def shutdown(self, save: Optional[Literal['save', 'nosave']] = None) -> Result[None]:
        """
        Synchronously save the dataset to disk and then shut down the server.
        """
        if save == 'save':
            return self._execute((b'SHUTDOWN', b'SAVE'), 'ok')
        elif save == 'nosave':
            return self._execute((b'SHUTDOWN', b'NOSAVE'), 'ok')
        else:
            return self._execute((b'SHUTDOWN',), 'ok')

    def slaveof(self, host: Optional[str], port: Optional[str] = None) -> Result[None]:
        """
        Make the server a slave of another instance, or promote it as master.

        Calling `slaveof(None)` will send `SLAVEOF NO ONE`.
        """
        if host is None:
            return self._execute((b'SLAVEOF', b'NO', b'ONE'), 'ok')
        else:
            command: List[ArgType] = [b'SLAVEOF', host]
            if port:
                command.append(port)
            return self._execute(command, 'ok')

    def slowlog_get(self, length: Optional[int] = None) -> Result[bytes]:
        """
        Returns the Redis slow queries log.
        """
        command: List[ArgType] = [b'SLOWLOG', b'GET']
        if length is not None:
            command.append(length)
        return self._execute(command, None)

    def slowlog_len(self) -> Result[int]:
        """
        Returns length of Redis slow queries log.
        """
        return self._execute((b'SLOWLOG', b'LEN'), 'int')

    def slowlog_reset(self) -> Result[None]:
        """
        Resets Redis slow queries log.
        """
        return self._execute((b'SLOWLOG', b'RESET',), 'ok')

    def sync(self) -> Result[bytes]:
        """
        Redis-server internal command used for replication.
        """
        return self._execute((b'SYNC',), None)

    def time(self) -> Result[datetime]:
        """
        Return current server time.
        """
        return apply_callback(self._execute((b'TIME',), 'int'), self._to_time)

    @staticmethod
    def _to_time(obj: Tuple[int, int]) -> datetime:
        s, ms = obj
        return datetime.fromtimestamp(s + ms / 1_000_000)
