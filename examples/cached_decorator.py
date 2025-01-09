import asyncio

from collections import namedtuple
import redis.asyncio as redis

from aiocache import cached
from aiocache import RedisCache
from aiocache.serializers import PickleSerializer

Result = namedtuple('Result', "content, status")

cache = RedisCache(namespace="main", client=redis.Redis(), serializer=PickleSerializer())

@cached(
    ttl=10, cache=cache, key_builder=lambda *args, **kw: "key")
async def cached_call():
    return Result("content", 200)


async def test_cached():
    async with cache:
        await cached_call()
        exists = await cache.exists("key")
        assert exists is True
        await cache.delete("key")


if __name__ == "__main__":
    asyncio.run(test_cached())
