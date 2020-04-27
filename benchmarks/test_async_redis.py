import async_redis


class TestAsyncRedis:
    package = 'async-redis'
    version = async_redis.VERSION

    @staticmethod
    async def run(set_queries: int, get_queries: int):
        async with async_redis.connect() as redis:
            for i in range(set_queries):
                await redis.set(f'foo_{i}', i)

            for i in range(get_queries):
                r = await redis.get(f'foo_{i}')
                assert r == str(i), r
