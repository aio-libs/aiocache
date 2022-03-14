import pytest

from aiocache import Cache
from aiocache.backends.redis import RedisBackend

# TODO: Update aioredis and fix tests.
collect_ignore_glob = ["*"]


@pytest.fixture
def redis_cache(event_loop):
    cache = Cache(Cache.REDIS, namespace="test", pool_max_size=1)
    yield cache

    for _, pool in RedisBackend.pools.items():
        pool.close()
        event_loop.run_until_complete(pool.wait_closed())


@pytest.fixture
def memcached_cache():
    cache = Cache(Cache.MEMCACHED, namespace="test", pool_size=1)
    yield cache
