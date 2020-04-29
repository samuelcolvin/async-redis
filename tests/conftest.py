import asyncio

from pytest import fixture

from async_redis import ConnectionSettings, Redis, connect
from async_redis.connection import RawConnection, create_raw_connection


@fixture(name='settings')
def fix_settings(loop):
    return ConnectionSettings()


@fixture(name='raw_connection')
def fix_raw_connection(loop, settings: ConnectionSettings):
    conn: RawConnection = loop.run_until_complete(create_raw_connection(settings))
    loop.run_until_complete(conn.execute([b'FLUSHALL']))
    yield conn
    loop.run_until_complete(conn.close())


@fixture(name='redis')
def fix_redis(loop, settings: ConnectionSettings):
    asyncio.set_event_loop(loop)
    conn: Redis = loop.run_until_complete(connect(settings))
    loop.run_until_complete(conn.flushall())
    yield conn
    loop.run_until_complete(conn.close())
