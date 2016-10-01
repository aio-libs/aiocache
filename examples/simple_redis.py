import asyncio

from aiocache import RedisCache


async def main():
    cache = RedisCache(endpoint="127.0.0.1", port=6379, namespace="default")
    await cache.set("key", "value")
    await cache.set("expire_me", "value", timeout=10)  # Key will expire after 10 secs
    print(await cache.get("key"))
    print(await cache.get("expire_me"))
    print(await cache.ttl("expire_me"))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
