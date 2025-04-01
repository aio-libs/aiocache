import pytest


@pytest.fixture
async def valkey_cache(valkey_client):
    # valkey connection pool raises ConnectionError but doesn't wait for conn reuse
    # when exceeding max pool size.
    from aiocache.backends.valkey import ValkeyCache
    async with ValkeyCache(namespace="test", client=valkey_client) as cache:
        yield cache


@pytest.fixture
async def memcached_cache():
    from aiocache.backends.memcached import MemcachedCache
    async with MemcachedCache(namespace="test", pool_size=1) as cache:
        yield cache
