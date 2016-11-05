import pytest
import asynctest

import aiocache

from aiocache import SimpleMemoryCache
from aiocache.serializers import DefaultSerializer
from aiocache.policies import DefaultPolicy
from aiocache.cache import BaseCache


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
    aiocache.set_defaults(
        cache=SimpleMemoryCache,
        serializer=DefaultSerializer,
        policy=DefaultPolicy,
        namespace="",
    )


@pytest.fixture
def mock_cache(mocker):
    mocker.patch('aiocache.cache.BaseCache.get_backend', return_value=asynctest.CoroutineMock())
    cache = BaseCache()
    mocker.spy(cache, '_build_key')
    mocker.spy(cache, '_serializer')
    cache.policy = asynctest.CoroutineMock()
    cache._backend.multi_get.return_value = ['a', 'b']
    return cache
