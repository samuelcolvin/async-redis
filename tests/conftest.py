from pytest import fixture

from async_redis import ConnectionSettings
from async_redis.connection import RawConnection, create_raw_connection


@fixture(name='raw_connection')
def fix_raw_connection(loop):
    s = ConnectionSettings()
    conn: RawConnection = loop.run_until_complete(create_raw_connection(s))
    loop.run_until_complete(conn.execute([b'FLUSHALL'], 'bytes'))
    yield conn
    loop.run_until_complete(conn.close())
