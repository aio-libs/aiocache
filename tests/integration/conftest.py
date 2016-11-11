import pytest

import aiocache

from aiocache import SimpleMemoryCache, RedisCache, MemcachedCache
from aiocache.policies import DefaultPolicy


def pytest_namespace():
    return {
        'KEY': "key",
        'KEY_1': "random"
    }


@pytest.fixture(autouse=True)
def reset_defaults():
    aiocache.settings.set_defaults(
        cache="aiocache.SimpleMemoryCache",
        serializer="aiocache.serializers.DefaultSerializer",
        policy="aiocache.policies.DefaultPolicy",
        namespace="",
    )


@pytest.fixture
def redis_cache(event_loop):
    cache = RedisCache(namespace="test", loop=event_loop)
    cache.set_policy(DefaultPolicy)
    yield cache

    event_loop.run_until_complete(cache.delete(pytest.KEY))
    event_loop.run_until_complete(cache.delete(pytest.KEY_1))

    cache._backend._pool.close()
    event_loop.run_until_complete(cache._backend._pool.wait_closed())


@pytest.fixture
def memory_cache(event_loop):
    cache = SimpleMemoryCache(namespace="test")
    cache.set_policy(DefaultPolicy)
    yield cache

    event_loop.run_until_complete(cache.delete(pytest.KEY))
    event_loop.run_until_complete(cache.delete(pytest.KEY_1))


@pytest.fixture
def memcached_cache(event_loop):
    cache = MemcachedCache(namespace="test", loop=event_loop)
    cache.set_policy(DefaultPolicy)
    yield cache

    event_loop.run_until_complete(cache.delete(pytest.KEY))
    event_loop.run_until_complete(cache.delete(pytest.KEY_1))
