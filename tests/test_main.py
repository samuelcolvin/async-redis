from async_redis import connect


async def test_simple():
    async with connect() as redis:
        assert None is await redis.set('foo', 123)
        assert '123' == await redis.get('foo')
