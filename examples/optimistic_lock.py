import asyncio
import logging
import random

from glide import GlideClientConfiguration, NodeAddress

from aiocache import ValkeyCache
from aiocache.lock import OptimisticLock, OptimisticLockError

logger = logging.getLogger(__name__)
addresses = [NodeAddress("localhost", 6379)]
config = GlideClientConfiguration(addresses=addresses, database_id=0)
cache = ValkeyCache(config, namespace="main")


async def expensive_function():
    logger.warning("Expensive is being executed...")
    await asyncio.sleep(random.uniform(0, 2))
    return "result"


async def my_view(cache):
    async with OptimisticLock(cache, "key") as lock:
        result = await expensive_function()
        try:
            await lock.cas(result)
        except OptimisticLockError:
            logger.warning(
                "I failed setting the value because it is different since the lock started!"
            )
        return result


async def concurrent():
    async with cache:
        await cache.set("key", "initial_value")
        # All three calls will read 'initial_value' as the value to check and only
        # the first one finishing will succeed because the others, when trying to set
        # the value, will see that the value is not the same as when the lock started
        await asyncio.gather(my_view(cache), my_view(cache), my_view(cache))


async def test_redis():
    await concurrent()
    async with ValkeyCache(config, namespace="main") as cache:
        await cache.delete("key")


if __name__ == "__main__":
    asyncio.run(test_redis())
