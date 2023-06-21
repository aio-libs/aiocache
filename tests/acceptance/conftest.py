import asyncio

import pytest

from aiocache import Cache, caches
from ..utils import KEY_LOCK, Keys


@pytest.fixture(autouse=True)
def reset_caches():
    caches._caches = {}
    caches.set_config(
        {
            "default": {
                "cache": "aiocache.SimpleMemoryCache",
                "serializer": {"class": "aiocache.serializers.NullSerializer"},
            }
        }
    )


@pytest.fixture
async def redis_cache():
    async with Cache(Cache.REDIS, namespace="test") as cache:
        yield cache
        await asyncio.gather(*(cache.delete(k) for k in (*Keys, KEY_LOCK)))


@pytest.fixture
async def memory_cache():
    async with Cache(namespace="test") as cache:
        yield cache
        await asyncio.gather(*(cache.delete(k) for k in (*Keys, KEY_LOCK)))


@pytest.fixture
async def memcached_cache():
    async with Cache(Cache.MEMCACHED, namespace="test") as cache:
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
