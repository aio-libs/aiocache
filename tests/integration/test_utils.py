import pytest
import aiocache
import asyncio

from aiocache import RedisCache, SimpleMemoryCache, cached
from aiocache.utils import get_default_cache
from aiocache.serializers import PickleSerializer, DefaultSerializer


class TestCachedDecorator:

    @pytest.mark.asyncio
    async def test_cached_no_args(self, mocker):
        mocker.spy(asyncio, 'sleep')
        cached_decorator = cached(ttl=10)

        resp1 = await cached_decorator(asyncio.sleep)(1)
        resp2 = await cached_decorator(asyncio.sleep)(1)

        assert asyncio.sleep.call_count == 1
        assert resp1 is resp2


class TestDefaultCache:

    @pytest.mark.asyncio
    async def test_default_cache_with_backend(self):

        cache = get_default_cache(
            backend=RedisCache, namespace="test", endpoint="http://...",
            port=6379, serializer=PickleSerializer())

        assert isinstance(cache, RedisCache)
        assert cache.namespace == "test"
        assert cache.endpoint == "http://..."
        assert cache.port == 6379
        assert isinstance(cache.serializer, PickleSerializer)

    @pytest.mark.asyncio
    async def test_default_cache_with_global(self):
        aiocache.config_default_cache(
            backend=RedisCache, namespace="test", endpoint="http://...",
            port=6379, serializer=PickleSerializer())
        cache = get_default_cache()

        assert isinstance(cache, RedisCache)
        assert cache.namespace == "test"
        assert cache.endpoint == "http://..."
        assert cache.port == 6379
        assert isinstance(cache.serializer, PickleSerializer)

        aiocache.default_cache = None

    @pytest.mark.asyncio
    async def test_default_cache_with_default(self):
        cache = get_default_cache(namespace="test")

        assert isinstance(cache, SimpleMemoryCache)
        assert cache.namespace == "test"
        assert isinstance(cache.serializer, DefaultSerializer)
