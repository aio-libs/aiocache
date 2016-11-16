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
    client_add = asynctest.CoroutineMock()
    client_get = asynctest.CoroutineMock()
    client_set = asynctest.CoroutineMock()
    client_multi_get = asynctest.CoroutineMock(return_value=['a', 'b'])
    client_multi_set = asynctest.CoroutineMock()
    client_delete = asynctest.CoroutineMock()
    client_exists = asynctest.CoroutineMock()
    client_clear = asynctest.CoroutineMock()
    client_raw = asynctest.CoroutineMock()


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
