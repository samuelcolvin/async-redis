import asyncio
import os
from datetime import datetime
from statistics import mean, stdev

import uvloop
from test_async_redis import TestAsyncRedis
from test_aioredis import TestAioredis


async def main():
    uvloop.install()
    classes = [TestAsyncRedis, TestAioredis]

    repeats = int(os.getenv('BENCHMARK_REPEATS', '5'))

    lpad = max(len(t.package) for t in classes) + 4
    print(f'testing {", ".join(t.package for t in classes)}, {repeats} times each')
    results = []

    set_queries, get_queries = 2_000, 2_000
    total_queries = set_queries + get_queries
    for test_class in classes:
        times = []
        p = test_class.package
        for i in range(repeats):
            start = datetime.now()
            await test_class.run(set_queries, get_queries)
            time = (datetime.now() - start).total_seconds()
            print(f'{p:>{lpad}} ({i + 1:>{len(str(repeats))}}/{repeats}) time={time:0.3f}s')
            times.append(time)

        print(f'{p:>{lpad}} best={min(times):0.3f}s, avg={mean(times):0.3f}s, stdev={stdev(times):0.3f}s')
        avg = mean(times) / total_queries * 1e6
        sd = stdev(times) / total_queries * 1e6
        results.append(f'{p:>{lpad}} best={min(times) / total_queries * 1e6:0.3f}μs/query '
                       f'avg={avg:0.3f}μs/query stdev={sd:0.3f}μs/query version={test_class.version}')
        print()

    for r in results:
        print(r)


if __name__ == '__main__':
    asyncio.run(main())
