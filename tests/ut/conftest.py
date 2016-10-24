import pytest
import asynctest

from aiocache import RedisCache, SimpleMemoryCache, MemcachedCache
from aiocache.serializers import DefaultSerializer


def pytest_namespace():
    return {
        'KEY': "key",
        'KEY_1': "random"
    }


async def dummy_pool(*args, **kwargs):
    class Pool:
        def __enter__(self):
            redis = asynctest.CoroutineMock()
            redis.mget = asynctest.CoroutineMock(return_value=[1, 2])
            redis.exists = asynctest.CoroutineMock(return_value=False)
            return redis

        def __exit__(self, *args, **kwargs):
            pass

    return Pool()


@pytest.fixture
def redis_mock_cache(event_loop, mocker):
    mocker.patch("aiocache.backends.redis.aioredis", asynctest.CoroutineMock())
    mocker.patch(
        "aiocache.backends.redis.RedisCache._connect",
        asynctest.CoroutineMock(side_effect=dummy_pool))

    cache = RedisCache(namespace="test:", loop=event_loop)
    cache._build_key = asynctest.MagicMock()
    mocker.spy(cache.serializer, 'loads')
    mocker.spy(cache.serializer, 'dumps')
    cache.policy = asynctest.CoroutineMock()
    yield cache


@pytest.fixture
def memcached_mock_cache(event_loop, mocker):
    mock_aiomcache = mocker.patch(
        "aiocache.backends.memcached.aiomcache", asynctest.MagicMock())
    mock_aiomcache.Client.return_value = asynctest.CoroutineMock()
    mock_aiomcache.Client.return_value.multi_get.return_value = ['a', 'b']

    cache = MemcachedCache(namespace="test:", loop=event_loop)
    cache._build_key = asynctest.MagicMock()
    mocker.spy(cache.serializer, 'loads')
    mocker.spy(cache.serializer, 'dumps')
    cache.policy = asynctest.CoroutineMock()
    yield cache


@pytest.fixture
def memory_mock_cache(event_loop, mocker):
    mocker.patch(
        "aiocache.backends.memory.SimpleMemoryCache._cache", asynctest.MagicMock())

    cache = SimpleMemoryCache(namespace="test:")
    cache._build_key = asynctest.MagicMock()
    mocker.spy(cache.serializer, 'loads')
    mocker.spy(cache.serializer, 'dumps')
    cache.policy = asynctest.CoroutineMock()
    yield cache


@pytest.fixture(params=[
    'redis_mock_cache',
    'memcached_mock_cache',
    'memory_mock_cache',
])
def mock_cache(request):
    return request.getfuncargvalue(request.param)
