import asyncio

import pytest

from ..utils import KEY_LOCK, Keys



@pytest.fixture
async def redis_cache(redis_client):
    from aiocache.backends.redis import RedisCache
    async with RedisCache(namespace="test", client=redis_client) as cache:
        yield cache
        await asyncio.gather(*(cache.delete(k) for k in (*Keys, KEY_LOCK)))


@pytest.fixture
async def memory_cache():
    from aiocache.backends.memory import SimpleMemoryCache
    async with SimpleMemoryCache(namespace="test") as cache:
        yield cache
        await asyncio.gather(*(cache.delete(k) for k in (*Keys, KEY_LOCK)))


@pytest.fixture
async def memcached_cache():
    from aiocache.backends.memcached import MemcachedCache
    async with MemcachedCache(namespace="test") as cache:
        yield cache
        await asyncio.gather(*(cache.delete(k) for k in (*Keys, KEY_LOCK)))


@pytest.fixture(
    params=(
        pytest.param("redis_cache", marks=pytest.mark.redis),
        "memory_cache",
        pytest.param("memcached_cache", marks=pytest.mark.memcached),
    ))
def cache(request):
    return request.getfixturevalue(request.param)
