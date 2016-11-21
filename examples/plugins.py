import asyncio
import random

from aiocache import RedisCache
from aiocache.plugins import HitMissRatioPlugin, TimingPlugin


cache = RedisCache(
    endpoint="127.0.0.1",
    plugins=[HitMissRatioPlugin(), TimingPlugin()],
    port=6379,
    namespace="main")


async def redis():
    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.set("c", 3)
    await cache.set("d", 4)

    possible_keys = ["a", "b", "c", "d", "e", "f"]

    for t in range(30):
        await cache.get(random.choice(possible_keys))

    assert cache.hit_miss_ratio["hit_ratio"] > 0.5
    assert cache.hit_miss_ratio["total"] == 30

    assert cache.profiling["get_min"] > 0
    assert cache.profiling["set_min"] > 0
    assert cache.profiling["get_max"] > 0
    assert cache.profiling["set_max"] > 0

    print(cache.hit_miss_ratio)
    print(cache.profiling)


def test_redis():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(redis())
    loop.run_until_complete(cache.delete("key"))
    loop.run_until_complete(cache.delete("expire_me"))


if __name__ == "__main__":
    test_redis()
