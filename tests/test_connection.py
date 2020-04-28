import pytest

from async_redis.connection import ConnectionSettings, RawConnection, create_raw_connection


async def test_connect():
    s = ConnectionSettings()
    conn = await create_raw_connection(s)
    try:
        r = await conn.execute([b'ECHO', b'hello'])
        assert r == b'hello'
    finally:
        await conn.close()


async def test_return_as_int(raw_connection: RawConnection):
    r = await raw_connection.execute([b'ECHO', 123], 'int')
    assert r == 123


async def test_return_as_int_list(raw_connection: RawConnection):
    assert 1 == await raw_connection.execute(['RPUSH', 'mylist', 1])
    assert 2 == await raw_connection.execute(['RPUSH', 'mylist', 2])
    assert 3 == await raw_connection.execute(['RPUSH', 'mylist', 3])
    r = await raw_connection.execute(['LRANGE', 'mylist', 0, -1], 'int')
    assert r == [1, 2, 3]


async def test_settings_repr():
    s = ConnectionSettings()
    assert repr(s) == "RedisSettings(host='localhost', port=6379, database=0, password=None, encoding='utf8')"
    assert str(s) == "RedisSettings(host='localhost', port=6379, database=0, password=None, encoding='utf8')"


async def test_encode_invalid(raw_connection: RawConnection):
    with pytest.raises(TypeError, match=r"Invalid argument: '\[1\]' <class 'list'> expected"):
        await raw_connection.execute([b'ECHO', [1]])
