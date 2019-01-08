import pytest
import asynctest

from aiocache.base import BaseCache, API
from aiocache import caches, RedisCache, MemcachedCache
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
        self._add = asynctest.CoroutineMock()
        self._get = asynctest.CoroutineMock()
        self._gets = asynctest.CoroutineMock()
        self._set = asynctest.CoroutineMock()
        self._multi_get = asynctest.CoroutineMock(return_value=["a", "b"])
        self._multi_set = asynctest.CoroutineMock()
        self._delete = asynctest.CoroutineMock()
        self._exists = asynctest.CoroutineMock()
        self._increment = asynctest.CoroutineMock()
        self._expire = asynctest.CoroutineMock()
        self._clear = asynctest.CoroutineMock()
        self._raw = asynctest.CoroutineMock()
        self._redlock_release = asynctest.CoroutineMock()
        self.acquire_conn = asynctest.CoroutineMock()
        self.release_conn = asynctest.CoroutineMock()
        self._close = asynctest.CoroutineMock()


@pytest.fixture
def mock_cache(mocker):
    cache = MockCache()
    cache.timeout = 0.002
    mocker.spy(cache, "_build_key")
    for cmd in API.CMDS:
        mocker.spy(cache, cmd.__name__)
    mocker.spy(cache, "close")
    cache.serializer = asynctest.Mock(spec=BaseSerializer)
    cache.serializer.encoding = "utf-8"
    cache.plugins = [asynctest.Mock(spec=BasePlugin)]
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
