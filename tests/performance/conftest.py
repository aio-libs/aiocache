import pytest

from aiocache import Cache


@pytest.fixture
async def redis_cache():
    # redis connection pool raises ConnectionError but doesn't wait for conn reuse
    #  when exceeding max pool size.
    cache = Cache(Cache.REDIS, namespace="test", pool_max_size=1)
    yield cache
    await cache.close()


@pytest.fixture
async def memcached_cache():
    cache = Cache(Cache.MEMCACHED, namespace="test", pool_size=1)
    yield cache
    await cache.close()
