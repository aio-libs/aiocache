import sys
import pytest
import aiocache
import random

from unittest import mock

from aiocache import RedisCache, SimpleMemoryCache, cached, multi_cached, config_default_cache
from aiocache.utils import get_default_cache
from aiocache.serializers import PickleSerializer, DefaultSerializer


async def return_dict(*args, keys=None):
    ret = {}
    for value, key in enumerate(keys or ['a', 'd', 'z', 'y']):
        ret[key] = value
    return ret

async def stub(*args, **kwargs):
    return random.randint(1, 50)


@pytest.fixture
def mock_cache(mocker):
    config_default_cache()
    cache = get_default_cache()
    mocker.spy(cache, 'multi_set')
    mocker.spy(cache, 'multi_get')
    mocker.spy(cache, 'get')
    mocker.spy(cache, 'exists')
    mocker.spy(cache, 'set')
    return cache


class TestCachedDecorator:

    @pytest.mark.asyncio
    async def test_cached_ttl(self, mocker, mock_cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')
        cached_decorator = cached(ttl=10)

        resp1 = await cached_decorator(stub)(1)
        resp2 = await cached_decorator(stub)(1)

        assert stub.call_count == 1
        assert resp1 is resp2

        mock_cache.get.assert_called_with('stubstub(1,){}')
        assert mock_cache.get.call_count == 1
        assert mock_cache.exists.call_count == 2
        mock_cache.set.assert_called_with('stubstub(1,){}', mock.ANY, ttl=10)
        assert mock_cache.set.call_count == 1

    @pytest.mark.asyncio
    async def test_cached_key_attribute(self, mocker, mock_cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')
        cached_decorator = cached(key_attribute="key")

        await cached_decorator(stub)(key='key')
        await cached_decorator(stub)(key='key')

        mock_cache.get.assert_called_with('key')
        mock_cache.set.assert_called_with('key', mock.ANY, ttl=0)


class TestMultiCachedDecorator:
    @pytest.mark.asyncio
    async def test_multi_cached(self, mocker):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'return_dict')
        cached_decorator = multi_cached(key_attribute='keys')

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

    @pytest.mark.asyncio
    async def test_multi_cached_key_attribute(self, mocker, mock_cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'return_dict')
        cached_decorator = multi_cached(key_attribute='keys')
        keys1 = {'a', 'b'}

        await cached_decorator(return_dict)(keys=keys1)
        mock_cache.multi_get.assert_called_once_with(keys1)
        mock_cache.multi_set.call_count = 1

    @pytest.mark.asyncio
    async def test_multi_cached_no_key_attribute(self, mocker, mock_cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'return_dict')
        cached_decorator = multi_cached()

        await cached_decorator(return_dict)()
        mock_cache.multi_set.call_count = 1


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
