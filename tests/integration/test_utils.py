import sys
import pytest
import aiocache
import asyncio

from aiocache import RedisCache, SimpleMemoryCache, cached, multi_cached
from aiocache.utils import get_default_cache
from aiocache.serializers import PickleSerializer, DefaultSerializer


async def return_dict(*args, keys=None):
    ret = {}
    for value, key in enumerate(keys or ['a', 'd', 'z', 'y']):
        ret[key] = value
    return ret


class TestCachedDecorator:

    @pytest.mark.asyncio
    async def test_cached_no_args(self, mocker):
        mocker.spy(asyncio, 'sleep')
        cached_decorator = cached(ttl=10)

        resp1 = await cached_decorator(asyncio.sleep)(1)
        resp2 = await cached_decorator(asyncio.sleep)(1)

        assert asyncio.sleep.call_count == 1
        assert resp1 is resp2


class TestMultiCachedDecorator:
    @pytest.mark.asyncio
    async def test_multi_cached_no_args(self, mocker):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'return_dict')
        cached_decorator = multi_cached()

        default_keys = {'a', 'd', 'z', 'y'}
        resp_default = await cached_decorator(return_dict)()
        return_dict.assert_called_with()
        assert default_keys == set(resp_default.keys())

        keys1 = {'a', 'b', 'c'}
        resp1 = await cached_decorator(return_dict)(keys=keys1)
        return_dict.assert_called_with(keys=list(keys1 - default_keys))
        assert keys1 == set(resp1.keys())

        keys2 = {'a', 'b', 'd', 'e', 'f'}
        resp2 = await cached_decorator(return_dict)(keys=keys2)
        return_dict.assert_called_with(keys=list(keys2 - keys1 - default_keys))
        assert keys2 == set(resp2.keys())


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
