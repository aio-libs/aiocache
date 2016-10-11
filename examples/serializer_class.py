import asyncio

from aiocache import RedisCache


class MySerializer:
    def dumps(self, value):
        return 1

    def loads(self, value):
        return 2


async def main():
    cache = RedisCache(serializer=MySerializer(), namespace="main:")
    await cache.set("key", "value")  # Will use MySerializer.dumps method
    print(await cache.get("key"))  # Will use MySerializer.loads method


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
