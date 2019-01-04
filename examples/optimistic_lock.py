import asyncio
import logging
import random

from aiocache import Cache
from aiocache.lock import OptimisticLock, OptimisticLockError


logger = logging.getLogger(__name__)
cache = Cache(Cache.REDIS, endpoint='127.0.0.1', port=6379, namespace='main')


async def expensive_function():
    logger.warning('Expensive is being executed...')
    await asyncio.sleep(random.uniform(0, 2))
    return 'result'


async def my_view():

    async with OptimisticLock(cache, 'key') as lock:
        result = await expensive_function()
        try:
            await lock.cas(result)
        except OptimisticLockError:
            logger.warning(
                'I failed setting the value because it is different since the lock started!')
        return result


async def concurrent():
    await cache.set('key', 'initial_value')
    # All three calls will read 'initial_value' as the value to check and only
    # the first one finishing will succeed because the others, when trying to set
    # the value, will see that the value is not the same as when the lock started
    await asyncio.gather(my_view(), my_view(), my_view())


def test_redis():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(concurrent())
    loop.run_until_complete(cache.delete('key'))
    loop.run_until_complete(cache.close())


if __name__ == '__main__':
    test_redis()
