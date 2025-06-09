import asyncio
from collections import namedtuple

from glide import GlideClientConfiguration, NodeAddress

from aiocache import ValkeyCache
from aiocache.serializers import PickleSerializer

MyObject = namedtuple("MyObject", ["x", "y"])
addresses = [NodeAddress("localhost", 6379)]
config = GlideClientConfiguration(addresses=addresses, database_id=0)


async def complex_object(cache):
    obj = MyObject(x=1, y=2)
    await cache.set("key", obj)
    my_object = await cache.get("key")

    assert my_object.x == 1
    assert my_object.y == 2


async def test_python_object():
    async with ValkeyCache(
        config, namespace="main", serializer=PickleSerializer()
    ) as cache:
        await complex_object(cache)
        await cache.delete("key")
        await cache.close()


if __name__ == "__main__":
    asyncio.run(test_python_object())
