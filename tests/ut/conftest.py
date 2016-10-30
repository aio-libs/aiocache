import pytest
import asynctest

from aiocache.cache import BaseCache


def pytest_namespace():
    return {
        'KEY': "key",
        'KEY_1': "random"
    }


@pytest.fixture
def mock_cache(mocker):
    mocker.patch('aiocache.cache.BaseCache.get_backend', return_value=asynctest.CoroutineMock())
    cache = BaseCache()
    mocker.spy(cache, '_build_key')
    mocker.spy(cache, '_serializer')
    cache.policy = asynctest.CoroutineMock()
    cache._backend.multi_get.return_value = ['a', 'b']
    return cache
