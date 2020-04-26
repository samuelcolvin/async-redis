from async_redis.connection import ConnectionSettings, create_raw_connection
from async_redis.typing import Decoders


async def test_connect():
    s = ConnectionSettings()
    conn = await create_raw_connection(s)
    try:
        r = await conn.execute([b'ECHO', b'hello'], Decoders.bytes)
        assert r == b'hello'
    finally:
        await conn.close()
