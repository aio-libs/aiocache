import asyncio
from typing import AsyncIterator

import pytest

from aiocache import BaseCache, Cache, caches
from ..utils import Keys, KEY_LOCK


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


async def _cache(cls_: BaseCache) -> AsyncIterator[Cache]:
    async with Cache(cls_, namespace="test") as cache:
        yield cache
        await asyncio.gather(*(cache.delete(k) for k in (*Keys, KEY_LOCK)))


@pytest.fixture
async def redis_cache():
    yield from _cache(Cache.REDIS)


@pytest.fixture
async def memory_cache():
    yield from _cache(Cache.MEMORY)


@pytest.fixture
async def memcached_cache():
    yield from _cache(Cache.MEMCACHED)


@pytest.fixture(params=("redis_cache", "memory_cache", "memcached_cache"))
def cache(request):
    return request.getfixturevalue(request.param)
