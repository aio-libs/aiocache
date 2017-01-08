import pytest

import aiocache

from aiocache import SimpleMemoryCache, RedisCache, MemcachedCache
from aiocache.backends import RedisBackend


def pytest_namespace():
    return {
        'KEY': "key",
        'KEY_1': "random"
    }


@pytest.fixture(autouse=True)
def reset_defaults():
    aiocache.settings.set_from_dict({
        "CACHE": {
            "class": "aiocache.SimpleMemoryCache",
        },
        "SERIALIZER": {
            "class": "aiocache.serializers.DefaultSerializer",
        },
        "PLUGIN": {
            "class": "aiocache.plugins.BasePlugin",
        }
    })


@pytest.fixture(autouse=True)
def reset_redis_pools(event_loop):
    RedisBackend.pools = {}


@pytest.fixture
def redis_cache(event_loop):
    cache = RedisCache(namespace="test", loop=event_loop)
    yield cache

    event_loop.run_until_complete(cache.delete(pytest.KEY))
    event_loop.run_until_complete(cache.delete(pytest.KEY_1))

    for _, pool in RedisBackend.pools.items():
        pool.close()
        event_loop.run_until_complete(pool.wait_closed())


@pytest.fixture
def memory_cache(event_loop):
    cache = SimpleMemoryCache(namespace="test")
    yield cache

    event_loop.run_until_complete(cache.delete(pytest.KEY))
    event_loop.run_until_complete(cache.delete(pytest.KEY_1))


@pytest.fixture
def memcached_cache(event_loop):
    cache = MemcachedCache(namespace="test", loop=event_loop)
    yield cache

    event_loop.run_until_complete(cache.delete(pytest.KEY))
    event_loop.run_until_complete(cache.delete(pytest.KEY_1))
