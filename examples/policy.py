import asyncio

from aiocache import RedisCache
from aiocache.policies import LRUPolicy


cache = RedisCache(namespace="main")
cache.policy = LRUPolicy(max_keys=2)


async def policy():
    await cache.set("key", "value")
    await cache.set("key_1", "value")
    await cache.set("key_2", "value")

    assert await cache.exists("key") is False
    assert await cache.exists("key_1") is True
    assert await cache.exists("key_2") is True


def test_policy():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(policy())
    loop.run_until_complete(cache.delete("key_1"))
    loop.run_until_complete(cache.delete("key_2"))


if __name__ == "__main__":
    test_policy()
