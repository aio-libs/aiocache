import pytest
import asynctest

import aiocache

from aiocache.cache import BaseCache, RedisCache
from aiocache.policies import DefaultPolicy
from aiocache.backends import SimpleMemoryBackend


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


@pytest.fixture
def mock_cache(mocker):
    mocker.patch(
        'aiocache.cache.BaseCache.get_backend',
        return_value=asynctest.Mock(spec=SimpleMemoryBackend))
    cache = BaseCache()
    cache._timeout = 0.002
    mocker.spy(cache, '_build_key')
    mocker.spy(cache, '_serializer')
    cache.policy = asynctest.Mock(spec=DefaultPolicy)
    cache._backend.multi_get.return_value = ['a', 'b']
    return cache


@pytest.fixture
def redis_cache(mocker, event_loop):
    mocker.patch(
        'aiocache.cache.RedisCache.get_backend',
        return_value=asynctest.Mock(spec=SimpleMemoryBackend))
    cache = RedisCache(loop=event_loop)
    return cache
