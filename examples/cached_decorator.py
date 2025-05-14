import asyncio
from collections import namedtuple

from glide import GlideClientConfiguration, NodeAddress

from aiocache import cached
from aiocache import ValkeyCache
from aiocache.serializers import PickleSerializer

Result = namedtuple("Result", "content, status")

addresses = [NodeAddress("localhost", 6379)]
config = GlideClientConfiguration(addresses=addresses, database_id=0)
cache = ValkeyCache(config=config, namespace="main", serializer=PickleSerializer())


@cached(cache, ttl=10, key_builder=lambda *args, **kw: "key")
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
