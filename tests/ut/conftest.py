import sys

if sys.version_info < (3, 8):
    # Missing AsyncMock on 3.7
    collect_ignore_glob = ["*"]

    from unittest.mock import Mock
    AsyncMock = Mock
else:
    from unittest.mock import AsyncMock, Mock

import pytest

from aiocache import caches
from aiocache.backends.memcached import MemcachedCache
from aiocache.backends.redis import RedisCache
from aiocache.base import API, BaseCache
from aiocache.plugins import BasePlugin
from aiocache.serializers import BaseSerializer


def pytest_configure():
    """
    Before pytest_namespace was being used to set the keys for
    testing but the feature was removed
    https://docs.pytest.org/en/latest/deprecations.html#pytest-namespace
    """
    pytest.KEY = "key"
    pytest.KEY_1 = "random"


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


class MockCache(BaseCache):
    def __init__(self):
        super().__init__()
        self._add = AsyncMock()
        self._get = AsyncMock()
        self._gets = AsyncMock()
        self._set = AsyncMock()
        self._multi_get = AsyncMock(return_value=["a", "b"])
        self._multi_set = AsyncMock()
        self._delete = AsyncMock()
        self._exists = AsyncMock()
        self._increment = AsyncMock()
        self._expire = AsyncMock()
        self._clear = AsyncMock()
        self._raw = AsyncMock()
        self._redlock_release = AsyncMock()
        self.acquire_conn = AsyncMock()
        self.release_conn = AsyncMock()
        self._close = AsyncMock()


@pytest.fixture
def mock_cache(mocker):
    cache = MockCache()
    cache.timeout = 0.002
    mocker.spy(cache, "_build_key")
    for cmd in API.CMDS:
        mocker.spy(cache, cmd.__name__)
    mocker.spy(cache, "close")
    cache.serializer = Mock(spec=BaseSerializer)
    cache.serializer.encoding = "utf-8"
    cache.plugins = [Mock(spec=BasePlugin)]
    return cache


@pytest.fixture
def base_cache():
    return BaseCache()


@pytest.fixture
def redis_cache():
    cache = RedisCache()
    return cache


@pytest.fixture
def memcached_cache():
    cache = MemcachedCache()
    return cache
