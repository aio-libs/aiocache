import asyncio

from aiocache import RedisCache
from aiocache.policies import LRUPolicy


async def main():
    cache = RedisCache(namespace="main:")
    cache.set_policy(LRUPolicy, max_keys=2)
    await cache.set("key", "value")
    await cache.set("key_1", "value")
    await cache.set("key_2", "value")
    print(cache.policy.dq)
    print(await cache.exists("key"))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
