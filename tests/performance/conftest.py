import pytest


@pytest.fixture
async def redis_cache(redis_client):
    # redis connection pool raises ConnectionError but doesn't wait for conn reuse
    # when exceeding max pool size.
    from aiocache.backends.redis import RedisCache
    async with RedisCache(namespace="test", client=redis_client) as cache:
        yield cache


@pytest.fixture
async def memcached_cache():
    from aiocache.backends.memcached import MemcachedCache
    async with MemcachedCache(namespace="test", pool_size=1) as cache:
        yield cache
