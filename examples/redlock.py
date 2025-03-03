import asyncio
import logging

import redis.asyncio as redis

from aiocache import RedisCache
from aiocache.lock import RedLock

logger = logging.getLogger(__name__)
cache = RedisCache(namespace="main", client=redis.Redis())


async def expensive_function():
    logger.warning('Expensive is being executed...')
    await asyncio.sleep(1)
    return 'result'


async def my_view():

    async with RedLock(cache, 'key', lease=2):  # Wait at most 2 seconds
        result = await cache.get('key')
        if result is not None:
            logger.info('Found the value in the cache hurray!')
            return result

        result = await expensive_function()
        await cache.set('key', result)
        return result


async def concurrent():
    await asyncio.gather(my_view(), my_view(), my_view())


async def test_redis():
    await concurrent()
    await cache.delete("key")
    await cache.close()


if __name__ == '__main__':
    asyncio.run(test_redis())
