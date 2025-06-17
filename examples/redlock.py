import asyncio
import logging

from glide import GlideClientConfiguration, NodeAddress

from aiocache import ValkeyCache
from aiocache.lock import RedLock

logger = logging.getLogger(__name__)
addresses = [NodeAddress("localhost", 6379)]
config = GlideClientConfiguration(addresses=addresses, database_id=0)


async def expensive_function():
    logger.warning("Expensive is being executed...")
    await asyncio.sleep(1)
    return "result"


async def my_view(cache):
    async with RedLock(cache, "key", lease=2):  # Wait at most 2 seconds
        result = await cache.get("key")
        if result is not None:
            logger.info("Found the value in the cache hurray!")
            return result

        result = await expensive_function()
        await cache.set("key", result)
        return result


async def concurrent(cache):
    await asyncio.gather(my_view(cache), my_view(cache), my_view(cache))


async def test_redis():
    async with ValkeyCache(config, namespace="main") as cache:
        await concurrent(cache)
        await cache.delete("key")
        await cache.close()


if __name__ == "__main__":
    asyncio.run(test_redis())
