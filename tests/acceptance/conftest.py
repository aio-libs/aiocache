import asyncio

import pytest

from ..utils import KEY_LOCK, Keys


@pytest.fixture
async def valkey_cache(valkey_config):
    from aiocache.backends.valkey import ValkeyCache

    async with ValkeyCache(valkey_config, namespace="test") as cache:
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
        pytest.param("valkey_cache", marks=pytest.mark.valkey),
        "memory_cache",
        pytest.param("memcached_cache", marks=pytest.mark.memcached),
    )
)
def cache(request):
    return request.getfixturevalue(request.param)
