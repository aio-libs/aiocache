import pytest

from aiocache import Cache, caches


def pytest_configure():
    """
    Before pytest_namespace was being used to set the keys for
    testing but the feature was removed
    https://docs.pytest.org/en/latest/deprecations.html#pytest-namespace
    """
    pytest.KEY = "key"
    pytest.KEY_1 = "random"


@pytest.fixture(autouse=True)
def reset_caches():
    caches._caches = {}
    caches.set_config(
        {
            "default": {
                "cache": "aiocache.SimpleMemoryCache",
                "serializer": {"class": "aiocache.serializers.NullSerializer"},
            }
        }
    )


@pytest.fixture
def redis_cache(event_loop):
    cache = Cache(Cache.REDIS, namespace="test")
    yield cache

    event_loop.run_until_complete(cache.delete(pytest.KEY))
    event_loop.run_until_complete(cache.delete(pytest.KEY_1))
    event_loop.run_until_complete(cache.delete(pytest.KEY + "-lock"))
    event_loop.run_until_complete(cache.close())


@pytest.fixture
def memory_cache(event_loop):
    cache = Cache(namespace="test")
    yield cache

    event_loop.run_until_complete(cache.delete(pytest.KEY))
    event_loop.run_until_complete(cache.delete(pytest.KEY_1))
    event_loop.run_until_complete(cache.delete(pytest.KEY + "-lock"))
    event_loop.run_until_complete(cache.close())


@pytest.fixture
def memcached_cache(event_loop):
    cache = Cache(Cache.MEMCACHED, namespace="test")
    yield cache

    event_loop.run_until_complete(cache.delete(pytest.KEY))
    event_loop.run_until_complete(cache.delete(pytest.KEY_1))
    event_loop.run_until_complete(cache.delete(pytest.KEY + "-lock"))
    event_loop.run_until_complete(cache.close())


@pytest.fixture(params=["redis_cache", "memory_cache", "memcached_cache"])
def cache(request):
    return request.getfixturevalue(request.param)
