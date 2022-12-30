import asyncio

from collections import namedtuple
from aiocache import Cache
from aiocache.serializers import PickleSerializer


MyObject = namedtuple("MyObject", ["x", "y"])
cache = Cache(Cache.REDIS, serializer=PickleSerializer(), namespace="main")


async def complex_object():
    obj = MyObject(x=1, y=2)
    await cache.set("key", obj)
    my_object = await cache.get("key")

    assert my_object.x == 1
    assert my_object.y == 2


async def test_python_object():
    await complex_object()
    await cache.delete("key")
    await cache.close()


if __name__ == "__main__":
    asyncio.run(test_python_object())
