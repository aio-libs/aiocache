import asyncio

from aiocache import Cache


cache = Cache(Cache.REDIS, endpoint="127.0.0.1", port=6379, namespace="main")


async def redis():
    await cache.set("key", "value")
    await cache.set("expire_me", "value", ttl=10)

    assert await cache.get("key") == "value"
    assert await cache.get("expire_me") == "value"
    assert await cache.raw("ttl", "main:expire_me") > 0


def test_redis():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(redis())
    loop.run_until_complete(cache.delete("key"))
    loop.run_until_complete(cache.delete("expire_me"))
    loop.run_until_complete(cache.close())


if __name__ == "__main__":
    test_redis()
