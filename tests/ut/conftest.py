import pytest
import asynctest

import aiocache

from aiocache.cache import RedisCache, BaseCache, MemcachedCache
from aiocache.backends import RedisBackend, MemcachedBackend, SimpleMemoryBackend
from aiocache.plugins import BasePlugin
from aiocache.serializers import DefaultSerializer


def pytest_namespace():
    return {
        'KEY': "key",
        'KEY_1': "random"
    }


@pytest.fixture(autouse=True)
def disable_logs(mocker):
    mocker.patch("aiocache.cache.logger")


@pytest.fixture(autouse=True)
def reset_instances():
    RedisBackend.instances = {}
    MemcachedBackend.instances = {}
    SimpleMemoryBackend.instances = {}


@pytest.fixture(autouse=True)
def reset_defaults():
    aiocache.settings.set_from_dict({
        "CACHE": {
            "class": "aiocache.SimpleMemoryCache",
        },
        "SERIALIZER": {
            "class": "aiocache.serializers.DefaultSerializer",
        },
        "PLUGINS": []
    })


class MockCache(BaseCache):
    _add = asynctest.CoroutineMock()
    _get = asynctest.CoroutineMock()
    _set = asynctest.CoroutineMock()
    _multi_get = asynctest.CoroutineMock(return_value=['a', 'b'])
    _multi_set = asynctest.CoroutineMock()
    _delete = asynctest.CoroutineMock()
    _exists = asynctest.CoroutineMock()
    _expire = asynctest.CoroutineMock()
    _clear = asynctest.CoroutineMock()
    _raw = asynctest.CoroutineMock()


@pytest.fixture
def mock_cache(mocker):
    cache = MockCache()
    cache._timeout = 0.002
    mocker.spy(cache, '_build_key')
    cache.serializer = asynctest.Mock(spec=DefaultSerializer)
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
