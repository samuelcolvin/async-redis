import aioredis


class TestAioredis:
    package = 'aioredis'
    version = aioredis.__version__

    @staticmethod
    async def run(set_queries: int, get_queries: int):
        redis = await aioredis.create_redis_pool('redis://localhost')
        await redis.set('my-key', 'value')
        for i in range(set_queries):
            await redis.set(f'foo_{i}', i)

        for i in range(get_queries):
            r = await redis.get(f'foo_{i}', encoding='utf-8')
            assert r == str(i), r

        redis.close()
        await redis.wait_closed()
