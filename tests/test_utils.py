import pytest
import aiocache

from aiocache import RedisCache, SimpleMemoryCache
from aiocache.utils import get_default_cache
from aiocache.serializers import PickleSerializer, DefaultSerializer


@pytest.mark.asyncio
async def test_default_cache_with_backend():

    cache = get_default_cache(
        backend=RedisCache, namespace="test", endpoint="http://...",
        port=6379, serializer=PickleSerializer())

    assert isinstance(cache, RedisCache)
    assert cache.namespace == "test"
    assert cache.endpoint == "http://..."
    assert cache.port == 6379
    assert isinstance(cache.serializer, PickleSerializer)


@pytest.mark.asyncio
async def test_default_cache_with_global():
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
async def test_default_cache_with_default():
    cache = get_default_cache(namespace="test")

    assert isinstance(cache, SimpleMemoryCache)
    assert cache.namespace == "test"
    assert isinstance(cache.serializer, DefaultSerializer)
