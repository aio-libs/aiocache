import asyncio

from collections import namedtuple

from aiocache import cached, RedisCache
from aiocache.serializers import PickleSerializer

Result = namedtuple('Result', "content, status")

RedisCache.set_defaults(
    namespace="main",
    db=1,
    pool_min_size=3,
    serializer=PickleSerializer())


@cached(cache=RedisCache, ttl=10, key="key")
async def decorator():
    return Result("content", 200)


async def global_cache():
    cache = RedisCache()
    obj = await cache.get("key")

    assert obj.content == "content"
    assert obj.status == 200
    assert cache.db == 1
    assert cache.pool_min_size == 3


def test_default_cache():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(decorator())
    loop.run_until_complete(global_cache())

    loop.run_until_complete(RedisCache(namespace="main").delete("key"))


if __name__ == "__main__":
    test_default_cache()
