import asyncio

from collections import namedtuple
import redis.asyncio as redis

from aiocache import cached, Cache
from aiocache.serializers import PickleSerializer
from examples.conftest import redis_kwargs_for_test

Result = namedtuple('Result', "content, status")


@cached(
    ttl=10, cache=Cache.REDIS, key_builder=lambda *args, **kw: "key",
    serializer=PickleSerializer(), namespace="main", client = redis.Redis(
        host="127.0.0.1",
        port=6379,
        db=0,
        decode_responses=False,
    ))
async def cached_call():
    return Result("content", 200)


async def test_cached():
    async with Cache(Cache.REDIS, namespace="main", client=redis.Redis(**redis_kwargs_for_test())) as cache:
        await cached_call()
        exists = await cache.exists("key")
        assert exists is True
        await cache.delete("key")


if __name__ == "__main__":
    asyncio.run(test_cached())
