import pytest

from aiocache import MemcachedCache, RedisCache
from aiocache.backends.redis import RedisBackend


@pytest.fixture
def redis_cache(event_loop):
    cache = RedisCache(
        namespace="test", loop=event_loop, pool_max_size=1)
    yield cache

    for _, pool in RedisBackend.pools.items():
        pool.close()
        event_loop.run_until_complete(pool.wait_closed())


@pytest.fixture
def memcached_cache(event_loop):
    cache = MemcachedCache(namespace="test", loop=event_loop, pool_size=1)
    yield cache
