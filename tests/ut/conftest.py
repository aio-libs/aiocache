import sys

if sys.version_info < (3, 8):
    # Missing AsyncMock on 3.7
    collect_ignore_glob = ["*"]

    from unittest.mock import Mock, create_autospec
    AsyncMock = Mock
else:
    from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from aiocache import caches
from aiocache.backends.memcached import MemcachedCache
from aiocache.backends.redis import RedisCache
from aiocache.base import API, BaseCache
from aiocache.plugins import BasePlugin
from aiocache.serializers import BaseSerializer


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
    cache = create_autospec(BaseCache, instance=True)
    #cache.timeout = 0.002
    #cache.serializer.encoding = "utf-8"
    #cache.plugins = [create_autospec(BasePlugin, instance=True)]
    return cache


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
