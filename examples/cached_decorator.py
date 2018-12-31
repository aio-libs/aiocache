import asyncio

from collections import namedtuple

from aiocache import cached, Cache
from aiocache.serializers import PickleSerializer

Result = namedtuple('Result', "content, status")


@cached(
    ttl=10, cache=Cache.REDIS, key="key", serializer=PickleSerializer(),
    port=6379, namespace="main")
async def cached_call():
    return Result("content", 200)


def test_cached():
    cache = Cache(Cache.REDIS, endpoint="127.0.0.1", port=6379, namespace="main")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cached_call())
    assert loop.run_until_complete(cache.exists("key")) is True
    loop.run_until_complete(cache.delete("key"))
    loop.run_until_complete(cache.close())


if __name__ == "__main__":
    test_cached()
