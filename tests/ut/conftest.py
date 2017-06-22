import pytest
import asynctest

from aiocache.base import BaseCache, API
from aiocache import caches, RedisCache, MemcachedCache
from aiocache.plugins import BasePlugin
from aiocache.serializers import NullSerializer


def pytest_namespace():
    return {
        'KEY': "key",
        'KEY_1': "random"
    }


@pytest.fixture(autouse=True)
def reset_caches():
    caches.set_config({
        'default': {
            'cache': "aiocache.SimpleMemoryCache",
            'serializer': {
                'class': "aiocache.serializers.NullSerializer"
            }
        }
    })


@pytest.fixture(autouse=True)
def disable_logs(mocker):
    mocker.patch("aiocache.log.logger")


class MockCache(BaseCache):

    def __init__(self):
        super().__init__()
        self._add = asynctest.CoroutineMock()
        self._get = asynctest.CoroutineMock()
        self._gets = asynctest.CoroutineMock()
        self._set = asynctest.CoroutineMock()
        self._multi_get = asynctest.CoroutineMock(return_value=['a', 'b'])
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
    mocker.spy(cache, '_build_key')
    for cmd in API.CMDS:
        mocker.spy(cache, cmd.__name__)
    mocker.spy(cache, "close")
    cache.serializer = asynctest.Mock(spec=NullSerializer)
    cache.plugins = [asynctest.Mock(spec=BasePlugin)]
    return cache


@pytest.fixture
def base_cache():
    return BaseCache()


@pytest.fixture
def redis_cache(event_loop):
    cache = RedisCache(loop=event_loop)
    return cache


@pytest.fixture
def memcached_cache(event_loop):
    cache = MemcachedCache(loop=event_loop)
    return cache
