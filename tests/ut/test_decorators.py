import asyncio
import sys
import pytest
import random
import inspect
import asynctest

from unittest import mock

from aiocache import cached, multi_cached, SimpleMemoryCache
from aiocache.decorators import _get_args_dict, _get_cache
from aiocache.serializers import DefaultSerializer


async def return_dict(keys=None):
    ret = {}
    for value, key in enumerate(keys or ['a', 'd', 'z', 'y']):
        ret[key] = str(value)
    return ret


async def empty_return(keys):
    return {}


async def raise_exception(*args, **kwargs):
    raise ValueError


async def stub(*args, key=None, seconds=0, **kwargs):
    await asyncio.sleep(seconds)
    if key:
        return str(key)
    return str(random.randint(1, 50))


class TestCachedDecorator:

    @pytest.fixture(autouse=True)
    def default_cache(self, mocker, mock_cache):
        mocker.patch("aiocache.decorators._get_cache", return_value=mock_cache)

    @pytest.mark.asyncio
    async def test_cached_ttl(self, mocker, mock_cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')
        mock_cache.get = asynctest.CoroutineMock(return_value=None)
        cached_decorator = cached(ttl=10)

        await cached_decorator(stub)(1)

        mock_cache.get.assert_called_with('stubstub(1,){}')
        mock_cache.set.assert_called_with('stubstub(1,){}', mock.ANY, ttl=10)

    @pytest.mark.asyncio
    async def test_cached_key_from_attr(self, mocker, mock_cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')
        cached_decorator = cached(key_from_attr="key")

        await cached_decorator(stub)(key='key')

        mock_cache.get.assert_called_with('key')

    @pytest.mark.asyncio
    async def test_cached_key(self, mocker, mock_cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')
        cached_decorator = cached(key="key")

        await cached_decorator(stub)()

        mock_cache.get.assert_called_with('key')

    @pytest.mark.asyncio
    async def test_cached_with_cache_exception_get(self, mocker, mock_cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')
        cached_decorator = cached(key="key")

        mock_cache.get = asynctest.CoroutineMock(side_effect=ConnectionRefusedError())

        await cached_decorator(stub)()
        assert stub.call_count == 1

    @pytest.mark.asyncio
    async def test_cached_with_cache_exception_set(self, mocker, mock_cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')
        mock_cache.get = asynctest.CoroutineMock(return_value=None)
        cached_decorator = cached(key="key")

        mock_cache.set = asynctest.CoroutineMock(side_effect=ConnectionRefusedError())

        await cached_decorator(stub)()
        assert stub.call_count == 1

    @pytest.mark.asyncio
    async def test_cached_func_exception(self, mocker, mock_cache):
        mock_cache.get = asynctest.CoroutineMock(return_value=None)
        cached_decorator = cached(key="key")

        with pytest.raises(ValueError):
            await cached_decorator(raise_exception)()

    @pytest.mark.asyncio
    async def test_cached_uses_class_instance(self, mocker, mock_cache):
        class Dummy:
            @cached()
            async def what(self):
                return "1"

            def __str__(self):
                return "Dummy"

        dummy = Dummy()
        await dummy.what()

        assert "Dummy" in mock_cache.get.call_args[0][0]

    @pytest.mark.asyncio
    async def test_cached_doesnt_uses_class_instance_when_noself(self, mocker, mock_cache):
        class Dummy:
            @cached(noself=True)
            async def what(self):
                return "1"

        dummy = Dummy()

        await dummy.what()
        mock_cache.get.assert_called_with('ut.test_decoratorswhat(){}')

    @pytest.mark.asyncio
    async def test_cached_from_alias(self, mocker, mock_cache):
        with asynctest.patch(
                "aiocache.decorators.caches.create",
                asynctest.MagicMock(return_value=mock_cache)) as mock_create:

            cached_decorator = cached(key="key", alias="whatever")
            await cached_decorator(stub)()

            mock_create.assert_called_with('whatever')
            mock_cache.get.assert_called_with('key')

    @pytest.mark.asyncio
    async def test_cached_alias_takes_precedence(self, mocker, mock_cache):
        with asynctest.patch(
                "aiocache.decorators.caches.create",
                asynctest.MagicMock(return_value=mock_cache)) as mock_create:

            cached_decorator = cached(key="key", alias="whatever", cache=SimpleMemoryCache)
            await cached_decorator(stub)()

            mock_create.assert_called_with('whatever')
            assert mock_cache.get.call_count == 1

    @pytest.mark.asyncio
    async def test_cached_keeps_signature(self):
        @cached()
        async def what(self, a, b):
            return "1"

        assert what.__name__ == "what"
        assert str(inspect.signature(what)) == '(self, a, b)'
        assert inspect.getfullargspec(what.__wrapped__).args == ['self', 'a', 'b']


class TestMultiCachedDecorator:

    @pytest.fixture(autouse=True)
    def default_cache(self, mocker, mock_cache):
        mocker.patch("aiocache.decorators._get_cache", return_value=mock_cache)

    @pytest.mark.asyncio
    async def test_multi_cached(self, mocker, mock_cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'return_dict')
        multi_cached_decorator = multi_cached('keys')

        default_keys = {'a', 'd', 'z', 'y'}
        mock_cache.multi_get = asynctest.CoroutineMock(return_value=[None, None, None, None])
        resp_default = await multi_cached_decorator(return_dict)(keys=default_keys)
        return_dict.assert_called_with(keys=list(default_keys))
        assert len(mock_cache.multi_set.call_args[0][0]) == len(default_keys)
        assert default_keys == set(resp_default.keys())

        keys1 = ['a', 'b', 'c']
        mock_cache.multi_get = asynctest.CoroutineMock(return_value=['a', None, None])
        resp1 = await multi_cached_decorator(return_dict)(keys=keys1)
        assert set(keys1) - default_keys == set(return_dict.call_args[1]['keys'])
        assert len(mock_cache.multi_set.call_args[0][0]) == len(set(keys1) - default_keys)
        assert set(keys1) == set(resp1.keys())

    @pytest.mark.asyncio
    async def test_multi_cached_keys_from_attr(self, mock_cache):
        keys1 = {'a', 'b'}
        mock_cache.multi_get = asynctest.CoroutineMock(return_value=[None, None])

        multi_cached_decorator = multi_cached(keys_from_attr='keys')
        await multi_cached_decorator(return_dict)(keys=keys1)

        mock_cache.multi_get.assert_called_with(list(keys1))
        assert mock_cache.multi_get.call_count == 1
        assert mock_cache.multi_set.call_count == 1

    @pytest.mark.asyncio
    async def test_multi_cached_empty_keys(self, mock_cache):
        multi_cached_decorator = multi_cached(keys_from_attr='keys')
        await multi_cached_decorator(return_dict)([])

        assert mock_cache.multi_get.call_count == 0
        assert mock_cache.multi_set.call_count == 1

    @pytest.mark.asyncio
    async def test_multi_cached_no_results(self, mock_cache):
        multi_cached_decorator = multi_cached(keys_from_attr='keys')
        resp = await multi_cached_decorator(empty_return)([])

        assert resp == {}

        assert mock_cache.multi_get.call_count == 0
        assert mock_cache.multi_set.call_count == 0

    @pytest.mark.asyncio
    async def test_multi_cached_no_keys_from_attr(self, mocker):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'return_dict')
        multi_cached_decorator = multi_cached("keys")

        with pytest.raises(KeyError):
            await multi_cached_decorator(return_dict)()

    @pytest.mark.asyncio
    async def test_multi_cached_with_cache_exception_get(self, mocker, mock_cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'return_dict')
        multi_cached_decorator = multi_cached(keys_from_attr='keys')

        mock_cache.multi_get = asynctest.CoroutineMock(side_effect=ConnectionRefusedError())

        await multi_cached_decorator(return_dict)(keys=['a', 'b'])
        assert return_dict.call_count == 1

    @pytest.mark.asyncio
    async def test_multi_cached_with_cache_exception_set(self, mocker, mock_cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'return_dict')
        multi_cached_decorator = multi_cached(keys_from_attr='keys')

        mock_cache.multi_set = asynctest.CoroutineMock(side_effect=ConnectionRefusedError())

        await multi_cached_decorator(return_dict)(keys=[])
        assert return_dict.call_count == 1

    @pytest.mark.asyncio
    async def test_multi_cached_func_exception(self, mocker):
        cached_decorator = multi_cached(keys_from_attr="keys")

        with pytest.raises(ValueError):
            await cached_decorator(raise_exception)(keys=[])

    @pytest.mark.asyncio
    async def test_multi_cached_from_alias(self, mocker, mock_cache):
        with asynctest.patch(
                "aiocache.decorators.caches.create",
                asynctest.MagicMock(return_value=mock_cache)) as mock_create:

            multi_cached_decorator = multi_cached(keys_from_attr='keys', alias="whatever")
            await multi_cached_decorator(return_dict)(keys=['key'])
            mock_create.assert_called_with('whatever')
            assert mock_cache.multi_get.call_count == 1
            assert mock_cache.multi_set.call_count == 0

    @pytest.mark.asyncio
    async def test_multi_cached_alias_takes_precedence(self, mocker, mock_cache):
        with asynctest.patch(
                "aiocache.decorators.caches.create",
                asynctest.MagicMock(return_value=mock_cache)) as mock_create:

            multi_cached_decorator = multi_cached(
                keys_from_attr='keys', alias="whatever", cache=SimpleMemoryCache)
            await multi_cached_decorator(return_dict)(keys=['key'])
            mock_create.assert_called_with('whatever')
            assert mock_cache.multi_get.call_count == 1

    @pytest.mark.asyncio
    async def test_multi_cached_keeps_signature(self):
        @multi_cached('keys')
        async def what(self, keys, a, b):
            return "1"

        assert what.__name__ == "what"
        assert str(inspect.signature(what)) == '(self, keys, a, b)'
        assert inspect.getfullargspec(what.__wrapped__).args == ['self', 'keys', 'a', 'b']


def test_get_args_dict():

    async def arg_return_dict(keys, dummy=None):
        ret = {}
        for value, key in enumerate(keys or ['a', 'd', 'z', 'y']):
            ret[key] = value
        return ret

    args = ({'b', 'a'},)

    assert _get_args_dict(arg_return_dict, args, {}) == {'dummy': None, 'keys': {'a', 'b'}}
    assert _get_args_dict(arg_return_dict, args, {'dummy': 'dummy'}) == \
        {'dummy': 'dummy', 'keys': {'a', 'b'}}
    assert _get_args_dict(arg_return_dict, [], {'dummy': 'dummy'}) == {'dummy': 'dummy'}


def test_get_cache():

    cache = _get_cache(SimpleMemoryCache, serializer=DefaultSerializer())

    assert isinstance(cache, SimpleMemoryCache)
    assert isinstance(cache.serializer, DefaultSerializer)
