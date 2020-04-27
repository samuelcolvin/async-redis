import asyncio

from line_profiler import LineProfiler

from async_redis.connection import RawConnection, create_raw_connection
from async_redis.main import Redis
from test_async_redis import TestAsyncRedis


async def run():
    await TestAsyncRedis.run(1000, 1000)


def run_sync():
    asyncio.run(run())


funcs_to_profile = [create_raw_connection]
module_objects = {**vars(RawConnection), **vars(Redis)}
funcs_to_profile += [v for v in module_objects.values() if str(v).startswith('<function')]
debug(funcs_to_profile)


def main():
    profiler = LineProfiler()
    for f in funcs_to_profile:
        profiler.add_function(f)
    profiler.wrap_function(run_sync)()
    profiler.print_stats(stripzeros=True)


if __name__ == '__main__':
    main()
