import pytest
import asynctest

import aiocache

from aiocache.cache import RedisCache, BaseCache
from aiocache.policies import DefaultPolicy
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
def reset_defaults():
    aiocache.settings.set_from_dict({
        "CACHE": {
            "class": "aiocache.SimpleMemoryCache",
        },
        "SERIALIZER": {
            "class": "aiocache.serializers.DefaultSerializer",
        },
        "POLICY": {
            "class": "aiocache.policies.DefaultPolicy",
        }
    })


class MockBackend:
    _add = asynctest.CoroutineMock()
    _get = asynctest.CoroutineMock()
    _set = asynctest.CoroutineMock()
    _multi_get = asynctest.CoroutineMock(return_value=['a', 'b'])
    _multi_set = asynctest.CoroutineMock()
    _delete = asynctest.CoroutineMock()
    _exists = asynctest.CoroutineMock()
    _clear = asynctest.CoroutineMock()
    _raw = asynctest.CoroutineMock()


class MockCache(MockBackend, BaseCache):
    pass


@pytest.fixture
def mock_cache(mocker):
    cache = MockCache()
    cache._timeout = 0.002
    mocker.spy(cache, '_build_key')
    cache.serializer = asynctest.Mock(spec=DefaultSerializer)
    cache.policy = asynctest.Mock(spec=DefaultPolicy)
    return cache


@pytest.fixture
def redis_cache(mocker, event_loop):
    cache = RedisCache(loop=event_loop)
    return cache
