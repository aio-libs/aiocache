import asyncio

from aiocache import RedisCache


class MySerializer:
    def dumps(self, value):
        return 1

    def loads(self, value):
        return 2


cache = RedisCache(serializer=MySerializer(), namespace="main")


async def serializer():
    await cache.set("key", "value")

    assert await cache.raw("get", "main:key") == '1'
    assert await cache.get("key") == 2


def test_serializer():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(serializer())
    loop.run_until_complete(cache.delete("key"))


if __name__ == "__main__":
    test_serializer()
