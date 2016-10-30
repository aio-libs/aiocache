"""
The module demonstrates the usage of the ``config_default_cache`` call. This call sets a default
cache for the whole aiocache package. Once called, all decorators will use the default cache (if
alternative cache is not set) and also it can be explicitly used with ``aiocache.default_cache``.
"""
import asyncio
import aiocache

from collections import namedtuple

from aiocache import cached

Result = namedtuple('Result', "content, status")

aiocache.config_default_cache()


@cached(ttl=10, key="key")
async def decorator():
    return Result("content", 200)


async def global_cache():
    obj = await aiocache.default_cache.get("key")

    assert obj.content == "content"
    assert obj.status == 200


def test_default_cache():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(decorator())
    loop.run_until_complete(global_cache())

    loop.run_until_complete(aiocache.default_cache.delete("key"))

if __name__ == "__main__":
    test_default_cache()
