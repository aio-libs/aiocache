import sys
from contextlib import ExitStack
from unittest.mock import create_autospec, patch

import pytest

from aiocache import caches
from aiocache.backends.memcached import MemcachedCache
from aiocache.backends.redis import RedisCache
from aiocache.base import BaseCache
from aiocache.plugins import BasePlugin

if sys.version_info < (3, 8):
    # Missing AsyncMock on 3.7
    collect_ignore_glob = ["*"]


@pytest.fixture(autouse=True)
def reset_caches():
    caches.set_config(
        {
            "default": {
                "cache": "aiocache.SimpleMemoryCache",
                "serializer": {"class": "aiocache.serializers.NullSerializer"},
            }
        }
    )


@pytest.fixture
def mock_cache(mocker):
    return create_autospec(BaseCache, instance=True)


@pytest.fixture
def mock_base_cache():
    """Return BaseCache instance with unimplemented methods mocked out."""
    plugin = create_autospec(BasePlugin, instance=True)
    cache = BaseCache(timeout=0.002, plugins=(plugin,))
    methods = ("_add", "_get", "_gets", "_set", "_multi_get", "_multi_set", "_delete",
               "_exists", "_increment", "_expire", "_clear", "_raw", "_close",
               "_redlock_release", "acquire_conn", "release_conn")
    with ExitStack() as stack:
        for f in methods:
            stack.enter_context(patch.object(cache, f, autospec=True))
        stack.enter_context(patch.object(cache, "_serializer", autospec=True))
        yield cache


@pytest.fixture
def base_cache():
    return BaseCache()


@pytest.fixture
async def redis_cache():
    async with RedisCache() as cache:
        yield cache


@pytest.fixture
async def memcached_cache():
    async with MemcachedCache() as cache:
        yield cache
