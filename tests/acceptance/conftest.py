import asyncio

import pytest
from tests.utils import Keys

from aiocache import Cache, caches


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


@pytest.fixture(params=(Cache.MEMORY, Cache.MEMCACHED, Cache.REDIS))
async def cache(request):
    cache = Cache(request.param, namespace="test")
    yield cache

    await asyncio.gather(*(cache.delete(k) for k in Keys))
    await cache.close()
