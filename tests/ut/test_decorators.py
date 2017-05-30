import asyncio
import sys
import pytest
import random
import inspect
import asynctest

from asynctest import CoroutineMock

from aiocache import cached, multi_cached, SimpleMemoryCache
from aiocache.decorators import _get_args_dict, _get_cache, cached_stampede
from aiocache.serializers import DefaultSerializer


async def stub(*args, value=None, seconds=0, **kwargs):
    await asyncio.sleep(seconds)
    if value:
        return str(value)
    return str(random.randint(1, 50))


class TestCached:

    @pytest.fixture
    def decorator(self, mocker, mock_cache):
        with asynctest.patch("aiocache.decorators._get_cache", return_value=mock_cache):
            yield cached()

    @pytest.fixture
    def decorator_call(self, decorator):
        yield decorator(stub)

    @pytest.fixture(autouse=True)
    def spy_stub(self, mocker):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')

    def test_init(self):
        c = cached(
            ttl=1, key="key", key_from_attr="key_attr", cache=SimpleMemoryCache,
            serializer=None, plugins=None, alias=None, noself=False, namespace="test")

        assert c.ttl == 1
        assert c.key == "key"
        assert c.key_from_attr == "key_attr"
        assert c.cache is None
        assert c._cache == SimpleMemoryCache

    def test_fails_at_instantiation(self):
        with pytest.raises(TypeError):
            @cached(wrong_param=1)
            async def fn(n):
                return n

    def test_alias_takes_precedence(self, mock_cache):
        with asynctest.patch(
                "aiocache.decorators.caches.create",
                asynctest.MagicMock(return_value=mock_cache)) as mock_create:
            c = cached(alias='default', cache=SimpleMemoryCache, namespace='test')
            c(stub)

            mock_create.assert_called_with('default')
            assert c.cache is mock_cache

    def test_get_cache_key_with_key(self, decorator):
        decorator.key = "key"
        decorator.key_from_attr = "ignore_me"
        assert decorator.get_cache_key(stub, (1, 2), {'a': 1, 'b': 2}) == 'key'

    def test_get_cache_key_with_key_attr(self, decorator):
        decorator.key_from_attr = "pick_me"
        assert decorator.get_cache_key(stub, (1, 2), {'pick_me': "key"}) == 'key'

    def test_get_cache_key_without_key_and_attr(self, decorator):
        assert decorator.get_cache_key(
            stub, (1, 2), {'a': 1, 'b': 2}) == "stub(1, 2)[('a', 1), ('b', 2)]"

    def test_get_cache_key_without_key_and_attr_noself(self, decorator):
        decorator.noself = True
        assert decorator.get_cache_key(
            stub, ('self', 1, 2), {'a': 1, 'b': 2}) == "stub(1, 2)[('a', 1), ('b', 2)]"

    @pytest.mark.asyncio
    async def test_calls_get_and_returns(self, decorator, decorator_call):
        decorator.cache.get = CoroutineMock(return_value=1)

        await decorator_call()

        decorator.cache.get.assert_called_with('stub()[]')
        assert decorator.cache.set.call_count == 0
        assert stub.call_count == 0

    @pytest.mark.asyncio
    async def test_get_from_cache_returns(self, decorator, decorator_call):
        decorator.cache.get = CoroutineMock(return_value=1)
        assert await decorator.get_from_cache("key") == 1
        assert decorator.cache.close.call_count == 1

    @pytest.mark.asyncio
    async def test_get_from_cache_exception(self, decorator, decorator_call):
        decorator.cache.get = CoroutineMock(side_effect=Exception)
        assert await decorator.get_from_cache("key") is None

    @pytest.mark.asyncio
    async def test_get_from_cache_none(self, decorator, decorator_call):
        decorator.cache.get = CoroutineMock(return_value=None)
        assert await decorator.get_from_cache("key") is None
        assert decorator.cache.close.call_count == 0

    @pytest.mark.asyncio
    async def test_calls_fn_set_when_get_none(self, decorator, decorator_call):
        decorator.cache.get = CoroutineMock(return_value=None)

        await decorator_call(value="value")

        assert decorator.cache.get.call_count == 1
        decorator.cache.set.assert_called_with("stub()[('value', 'value')]", "value", ttl=None)
        assert stub.call_count == 1

    @pytest.mark.asyncio
    async def test_set_calls_set(self, decorator, decorator_call):
        await decorator.set_in_cache("key", "value")
        decorator.cache.set.assert_called_with("key", "value", ttl=None)

    @pytest.mark.asyncio
    async def test_set_calls_set_ttl(self, decorator, decorator_call):
        decorator.ttl = 10
        await decorator.set_in_cache("key", "value")
        decorator.cache.set.assert_called_with("key", "value", ttl=10)

    @pytest.mark.asyncio
    async def test_set_catches_exception(self, decorator, decorator_call):
        decorator.cache.set = CoroutineMock(side_effect=Exception)
        assert await decorator.set_in_cache("key", "value") is None

    @pytest.mark.asyncio
    async def test_decorate(self):

        @cached()
        async def fn(n):
            return n

        assert await fn(1) == 1
        assert await fn(2) == 2

    @pytest.mark.asyncio
    async def test_cached_keeps_signature(self):
        @cached()
        async def what(self, a, b):
            return "1"

        assert what.__name__ == "what"
        assert str(inspect.signature(what)) == '(self, a, b)'
        assert inspect.getfullargspec(what.__wrapped__).args == ['self', 'a', 'b']


class TestCachedStampede:
    @pytest.fixture
    def decorator(self, mocker, mock_cache):
        with asynctest.patch("aiocache.decorators._get_cache", return_value=mock_cache):
            yield cached_stampede()

    @pytest.fixture
    def decorator_call(self, decorator):
        yield decorator(stub)

    @pytest.fixture(autouse=True)
    def spy_stub(self, mocker):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')

    def test_inheritance(self):
        assert isinstance(cached_stampede(), cached)

    def test_init(self):
        c = cached_stampede(
            lease=3, ttl=1, key="key", key_from_attr="key_attr", cache=SimpleMemoryCache,
            serializer=None, plugins=None, alias=None, noself=False, namespace="test")

        assert c.ttl == 1
        assert c.key == "key"
        assert c.key_from_attr == "key_attr"
        assert c.cache is None
        assert c._cache == SimpleMemoryCache
        assert c.lease == 3

    @pytest.mark.asyncio
    async def test_calls_get_and_returns(self, decorator, decorator_call):
        decorator.cache.get = CoroutineMock(return_value=1)

        await decorator_call()

        decorator.cache.get.assert_called_with('stub()[]')
        assert decorator.cache.set.call_count == 0
        assert stub.call_count == 0

    @pytest.mark.asyncio
    async def test_calls_redlock(self, decorator, decorator_call):
        decorator.cache.get = CoroutineMock(return_value=None)

        await decorator_call(value="value")

        assert decorator.cache.get.call_count == 2
        assert decorator.cache._redlock.call_count == 1
        decorator.cache.set.assert_called_with("stub()[('value', 'value')]", "value", ttl=None)
        assert stub.call_count == 1

    @pytest.mark.asyncio
    async def test_calls_locked_client(self, decorator, decorator_call):
        decorator.cache.get = CoroutineMock(side_effect=[None, None, None, "value"])
        decorator.cache._add = CoroutineMock(side_effect=[True, ValueError])
        decorator.cache._redlock_release = CoroutineMock(side_effect=[1, 0])

        await asyncio.gather(decorator_call(value="value"), decorator_call(value="value"))

        assert decorator.cache.get.call_count == 4
        assert decorator.cache._redlock.call_count == 2
        decorator.cache.set.assert_called_with("stub()[('value', 'value')]", "value", ttl=None)
        assert stub.call_count == 1


async def return_dict(keys=None):
    ret = {}
    for value, key in enumerate(keys or ['a', 'd', 'z', 'y']):
        ret[key] = str(value)
    return ret


async def empty_return(keys):
    return {}


async def raise_exception(*args, **kwargs):
    raise ValueError


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


def test_get_cache_fails_on_wrong_arg():
    with pytest.raises(TypeError):
        _get_cache(SimpleMemoryCache, wrong_arg=1)
