import asyncio
import aiocache

from collections import namedtuple

from aiocache import cached, RedisCache
from aiocache.serializers import PickleSerializer

Result = namedtuple('Result', "content, status")

aiocache.set_defaults(cache=RedisCache, serializer=PickleSerializer)


@cached(ttl=10, key="key", namespace="main")
async def decorator():
    return Result("content", 200)


async def global_cache():
    obj = await RedisCache(namespace="main").get("key")

    assert obj.content == "content"
    assert obj.status == 200


def test_default_cache():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(decorator())
    loop.run_until_complete(global_cache())

    loop.run_until_complete(RedisCache(namespace="main").delete("key"))

if __name__ == "__main__":
    test_default_cache()
