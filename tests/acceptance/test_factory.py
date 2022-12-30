import pytest

from aiocache import Cache
from aiocache.backends.memcached import MemcachedCache
from aiocache.backends.memory import SimpleMemoryCache
from aiocache.backends.redis import RedisCache


class TestCache:
    async def test_from_url_memory(self):
        async with Cache.from_url("memory://") as cache:
            assert isinstance(cache, SimpleMemoryCache)

    def test_from_url_memory_no_endpoint(self):
        with pytest.raises(TypeError):
            Cache.from_url("memory://endpoint:10")

    async def test_from_url_redis(self):
        url = ("redis://endpoint:1000/0/?password=pass"
               + "&pool_max_size=50&create_connection_timeout=20")

        async with Cache.from_url(url) as cache:
            assert isinstance(cache, RedisCache)
            assert cache.endpoint == "endpoint"
            assert cache.port == 1000
            assert cache.password == "pass"
            assert cache.pool_max_size == 50
            assert cache.create_connection_timeout == 20

    async def test_from_url_memcached(self):
        url = "memcached://endpoint:1000?pool_size=10"

        async with Cache.from_url(url) as cache:
            assert isinstance(cache, MemcachedCache)
            assert cache.endpoint == "endpoint"
            assert cache.port == 1000
            assert cache.pool_size == 10

    @pytest.mark.parametrize("scheme", ("memory", "redis", "memcached"))
    def test_from_url_unexpected_param(self, scheme):
        with pytest.raises(TypeError):
            Cache.from_url("{}://?arg1=arg1".format(scheme))
