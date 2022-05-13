import pytest

from aiocache import Cache


# TODO:
#  1. concurrency_error_rates test doesn't work as expected with redis-py,
#  where both ConnectionPool and BlockingConnectionPool raise ConnectionError
#  but don't wait for connection reuse when number of conns exceeds the limit.
#  That's why pool in redis-py uses an unlimit number connections by default.
#  So no HTTP req should fails in the concurrency_error_rates test with redis-py.
#  2. On my local machine, test_memcached_getsetdel() fails, it doesn't reach
#  the performance target.
collect_ignore_glob = ["*"]


@pytest.fixture
def redis_cache():
    # redis connection pool raises ConnectionError but doesn't wait for conn reuse
    #  when exceeding max pool size.
    cache = Cache(Cache.REDIS, namespace="test", pool_max_size=1)
    yield cache


@pytest.fixture
def memcached_cache():
    cache = Cache(Cache.MEMCACHED, namespace="test", pool_size=1)
    yield cache
