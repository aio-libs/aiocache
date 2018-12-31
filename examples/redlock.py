import asyncio
import logging

from aiocache import Cache
from aiocache.lock import RedLock


logger = logging.getLogger(__name__)
cache = Cache(Cache.REDIS, endpoint='127.0.0.1', port=6379, namespace='main')


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


def test_redis():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(concurrent())
    loop.run_until_complete(cache.delete('key'))
    loop.run_until_complete(cache.close())


if __name__ == '__main__':
    test_redis()
