from async_redis import Redis


async def test_simple(redis: Redis):
    async with redis.pipeline() as p:
        p.set('foo', 1)
        p.set('bar', 2)
        p.get('foo')
        p.set('foo', 3)
        p.get('foo')
        # v = await p.execute()
    # debug(v)
