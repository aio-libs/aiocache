import asyncio

from collections import namedtuple
from aiocache import RedisCache
from aiocache.serializers import PickleSerializer


MyObject = namedtuple("MyObject", ["x", "y"])


async def main():
    cache = RedisCache(serializer=PickleSerializer(), namespace="default:")
    # This will serialize to pickle and store in redis with bytes format
    await cache.set("key", MyObject(x=1, y=2))
    # This will retrieve the object and deserialize back to MyObject
    my_object = await cache.get("key")
    print("MyObject x={}, y={}".format(my_object.x, my_object.y))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
