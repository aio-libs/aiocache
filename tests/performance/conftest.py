import pytest

from aiocache import Cache


@pytest.fixture
async def redis_cache():
    # redis connection pool raises ConnectionError but doesn't wait for conn reuse
    #  when exceeding max pool size.
    async with Cache(Cache.REDIS, namespace="test", pool_max_size=1) as cache:
        yield cache


@pytest.fixture
async def memcached_cache():
    async with Cache(Cache.MEMCACHED, namespace="test", pool_size=1) as cache:
        yield cache
