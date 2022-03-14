import asyncio
import inspect
import random
import sys
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from aiocache import cached, cached_stampede, multi_cached
from aiocache.backends.memory import SimpleMemoryCache
from aiocache.base import BaseCache, SENTINEL
from aiocache.decorators import _get_args_dict
from aiocache.lock import RedLock


async def stub(*args, value=None, seconds=0, **kwargs):
    await asyncio.sleep(seconds)
    if value:
        return str(value)
    return str(random.randint(1, 50))


class TestCached:
    @pytest.fixture
    def decorator(self, mocker, mock_cache):
        with patch("aiocache.decorators._get_cache", return_value=mock_cache):
            yield cached()

    @pytest.fixture
    def decorator_call(self, decorator):
        d = decorator(stub)
        yield d

    @pytest.fixture(autouse=True)
    def spy_stub(self, mocker):
        module = sys.modules[globals()["__name__"]]
        mocker.spy(module, "stub")

    def test_init(self):
        c = cached(
            ttl=1,
            key="key",
            key_builder="fn",
            cache=SimpleMemoryCache,
            plugins=None,
            alias=None,
            noself=False,
            namespace="test",
        )

        assert c.ttl == 1
        assert c.key == "key"
        assert c.key_builder == "fn"
        assert c.cache is None
        assert c._cache == SimpleMemoryCache
        assert c._serializer is None
        assert c._kwargs == {"namespace": "test"}

    def test_fails_at_instantiation(self):
        with pytest.raises(TypeError):

            @cached(wrong_param=1)
            async def fn(n):
                return n

    def test_alias_takes_precedence(self, mock_cache):
        with patch(
            "aiocache.decorators.caches.get", MagicMock(return_value=mock_cache)
        ) as mock_get:
            c = cached(alias="default", cache=SimpleMemoryCache, namespace="test")
            c(stub)

            mock_get.assert_called_with("default")
            assert c.cache is mock_cache

    def test_get_cache_key_with_key(self, decorator):
        decorator.key = "key"
        decorator.key_builder = "fn"
        assert decorator.get_cache_key(stub, (1, 2), {"a": 1, "b": 2}) == "key"

    def test_get_cache_key_without_key_and_attr(self, decorator):
        assert (
            decorator.get_cache_key(stub, (1, 2), {"a": 1, "b": 2})
            == "stub(1, 2)[('a', 1), ('b', 2)]"
        )

    def test_get_cache_key_without_key_and_attr_noself(self, decorator):
        decorator.noself = True
        assert (
            decorator.get_cache_key(stub, ("self", 1, 2), {"a": 1, "b": 2})
            == "stub(1, 2)[('a', 1), ('b', 2)]"
        )

    def test_get_cache_key_with_key_builder(self, decorator):
        decorator.key_builder = lambda *args, **kwargs: kwargs["market"].upper()
        assert decorator.get_cache_key(stub, (), {"market": "es"}) == "ES"

    @pytest.mark.asyncio
    async def test_calls_get_and_returns(self, decorator, decorator_call):
        decorator.cache.get = AsyncMock(return_value=1)

        await decorator_call()

        decorator.cache.get.assert_called_with("stub()[]")
        assert decorator.cache.set.call_count == 0
        assert stub.call_count == 0

    @pytest.mark.asyncio
    async def test_cache_read_disabled(self, decorator, decorator_call):
        await decorator_call(cache_read=False)

        assert decorator.cache.get.call_count == 0
        assert decorator.cache.set.call_count == 1
        assert stub.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_write_disabled(self, decorator, decorator_call):
        decorator.cache.get = AsyncMock(return_value=None)

        await decorator_call(cache_write=False)

        assert decorator.cache.get.call_count == 1
        assert decorator.cache.set.call_count == 0
        assert stub.call_count == 1

    @pytest.mark.asyncio
    async def test_disable_params_not_propagated(self, decorator, decorator_call):
        decorator.cache.get = AsyncMock(return_value=None)

        await decorator_call(cache_read=False, cache_write=False)

        stub.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_get_from_cache_returns(self, decorator, decorator_call):
        decorator.cache.get = AsyncMock(return_value=1)
        assert await decorator.get_from_cache("key") == 1

    @pytest.mark.asyncio
    async def test_get_from_cache_exception(self, decorator, decorator_call):
        decorator.cache.get = AsyncMock(side_effect=Exception)
        assert await decorator.get_from_cache("key") is None

    @pytest.mark.asyncio
    async def test_get_from_cache_none(self, decorator, decorator_call):
        decorator.cache.get = AsyncMock(return_value=None)
        assert await decorator.get_from_cache("key") is None

    @pytest.mark.asyncio
    async def test_calls_fn_set_when_get_none(self, mocker, decorator, decorator_call):
        mocker.spy(decorator, "get_from_cache")
        mocker.spy(decorator, "set_in_cache")
        decorator.cache.get = AsyncMock(return_value=None)

        await decorator_call(value="value")

        assert decorator.get_from_cache.call_count == 1
        decorator.set_in_cache.assert_called_with("stub()[('value', 'value')]", "value")
        stub.assert_called_once_with(value="value")

    @pytest.mark.asyncio
    async def test_calls_fn_raises_exception(self, mocker, decorator, decorator_call):
        decorator.cache.get = AsyncMock(return_value=None)
        stub.side_effect = Exception()
        with pytest.raises(Exception):
            assert await decorator_call()

    @pytest.mark.asyncio
    async def test_cache_write_waits_for_future(self, mocker, decorator, decorator_call):
        decorator.get_from_cache = AsyncMock(return_value=None)
        decorator.set_in_cache = AsyncMock()
        await decorator_call()

        decorator.set_in_cache.assert_awaited()

    @pytest.mark.asyncio
    async def test_cache_write_doesnt_wait_for_future(self, mocker, decorator, decorator_call):
        decorator.get_from_cache = AsyncMock(return_value=None)
        decorator.set_in_cache = AsyncMock()

        with patch("aiocache.decorators.asyncio.ensure_future"):
            await decorator_call(aiocache_wait_for_write=False, value="value")

        decorator.set_in_cache.assert_not_awaited()
        decorator.set_in_cache.assert_called_once_with("stub()[('value', 'value')]", "value")

    @pytest.mark.asyncio
    async def test_set_calls_set(self, decorator, decorator_call):
        await decorator.set_in_cache("key", "value")
        decorator.cache.set.assert_called_with("key", "value", ttl=SENTINEL)

    @pytest.mark.asyncio
    async def test_set_calls_set_ttl(self, decorator, decorator_call):
        decorator.ttl = 10
        await decorator.set_in_cache("key", "value")
        decorator.cache.set.assert_called_with("key", "value", ttl=decorator.ttl)

    @pytest.mark.asyncio
    async def test_set_catches_exception(self, decorator, decorator_call):
        decorator.cache.set = AsyncMock(side_effect=Exception)
        assert await decorator.set_in_cache("key", "value") is None

    @pytest.mark.asyncio
    async def test_decorate(self, mock_cache):
        mock_cache.get = AsyncMock(return_value=None)
        with patch("aiocache.decorators._get_cache", return_value=mock_cache):

            @cached()
            async def fn(n):
                return n

            assert await fn(1) == 1
            assert await fn(2) == 2
            assert fn.cache == mock_cache

    @pytest.mark.asyncio
    async def test_keeps_signature(self, mock_cache):
        with patch("aiocache.decorators._get_cache", return_value=mock_cache):

            @cached()
            async def what(self, a, b):
                return "1"

            assert what.__name__ == "what"
            assert str(inspect.signature(what)) == "(self, a, b)"
            assert inspect.getfullargspec(what.__wrapped__).args == ["self", "a", "b"]

    @pytest.mark.asyncio
    async def test_reuses_cache_instance(self):
        with patch("aiocache.decorators._get_cache") as get_c:
            cache = MagicMock(spec=BaseCache)
            get_c.side_effect = [cache, None]

            @cached()
            async def what():
                pass

            await what()
            await what()

            assert get_c.call_count == 1
            assert cache.get.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_per_function(self):
        @cached()
        async def foo():
            pass

        @cached()
        async def bar():
            pass

        assert foo.cache != bar.cache


class TestCachedStampede:
    @pytest.fixture
    def decorator(self, mocker, mock_cache):
        with patch("aiocache.decorators._get_cache", return_value=mock_cache):
            yield cached_stampede()

    @pytest.fixture
    def decorator_call(self, decorator):
        yield decorator(stub)

    @pytest.fixture(autouse=True)
    def spy_stub(self, mocker):
        module = sys.modules[globals()["__name__"]]
        mocker.spy(module, "stub")

    def test_inheritance(self):
        assert isinstance(cached_stampede(), cached)

    def test_init(self):
        c = cached_stampede(
            lease=3,
            ttl=1,
            key="key",
            key_builder="fn",
            cache=SimpleMemoryCache,
            plugins=None,
            alias=None,
            noself=False,
            namespace="test",
        )

        assert c.ttl == 1
        assert c.key == "key"
        assert c.key_builder == "fn"
        assert c.cache is None
        assert c._cache == SimpleMemoryCache
        assert c._serializer is None
        assert c.lease == 3
        assert c._kwargs == {"namespace": "test"}

    @pytest.mark.asyncio
    async def test_calls_get_and_returns(self, decorator, decorator_call):
        decorator.cache.get = AsyncMock(return_value=1)

        await decorator_call()

        decorator.cache.get.assert_called_with("stub()[]")
        assert decorator.cache.set.call_count == 0
        assert stub.call_count == 0

    @pytest.mark.asyncio
    async def test_calls_fn_raises_exception(self, mocker, decorator, decorator_call):
        decorator.cache.get = AsyncMock(return_value=None)
        stub.side_effect = Exception()
        with pytest.raises(Exception):
            assert await decorator_call()

    @pytest.mark.asyncio
    async def test_calls_redlock(self, decorator, decorator_call):
        decorator.cache.get = AsyncMock(return_value=None)
        lock = MagicMock(spec=RedLock)

        with patch("aiocache.decorators.RedLock", return_value=lock):
            await decorator_call(value="value")

            assert decorator.cache.get.call_count == 2
            assert lock.__aenter__.call_count == 1
            assert lock.__aexit__.call_count == 1
            decorator.cache.set.assert_called_with(
                "stub()[('value', 'value')]", "value", ttl=SENTINEL
            )
            stub.assert_called_once_with(value="value")

    @pytest.mark.asyncio
    async def test_calls_locked_client(self, decorator, decorator_call):
        decorator.cache.get = AsyncMock(side_effect=[None, None, None, "value"])
        decorator.cache._add = AsyncMock(side_effect=[True, ValueError])
        lock1 = MagicMock(spec=RedLock)
        lock2 = MagicMock(spec=RedLock)

        with patch("aiocache.decorators.RedLock", side_effect=[lock1, lock2]):
            await asyncio.gather(decorator_call(value="value"), decorator_call(value="value"))

            assert decorator.cache.get.call_count == 4
            assert lock1.__aenter__.call_count == 1
            assert lock1.__aexit__.call_count == 1
            assert lock2.__aenter__.call_count == 1
            assert lock2.__aexit__.call_count == 1
            decorator.cache.set.assert_called_with(
                "stub()[('value', 'value')]", "value", ttl=SENTINEL
            )
            assert stub.call_count == 1


async def stub_dict(*args, keys=None, **kwargs):
    values = {"a": random.randint(1, 50), "b": random.randint(1, 50), "c": random.randint(1, 50)}
    return {k: values.get(k) for k in keys}


class TestMultiCached:
    @pytest.fixture
    def decorator(self, mocker, mock_cache):
        with patch("aiocache.decorators._get_cache", return_value=mock_cache):
            yield multi_cached(keys_from_attr="keys")

    @pytest.fixture
    def decorator_call(self, decorator):
        d = decorator(stub_dict)
        decorator._conn = decorator.cache.get_connection()
        yield d

    @pytest.fixture(autouse=True)
    def spy_stub_dict(self, mocker):
        module = sys.modules[globals()["__name__"]]
        mocker.spy(module, "stub_dict")

    def test_init(self):
        mc = multi_cached(
            keys_from_attr="keys",
            key_builder=None,
            ttl=1,
            cache=SimpleMemoryCache,
            plugins=None,
            alias=None,
            namespace="test",
        )

        assert mc.ttl == 1
        assert mc.key_builder("key", lambda x: x) == "key"
        assert mc.keys_from_attr == "keys"
        assert mc.cache is None
        assert mc._cache == SimpleMemoryCache
        assert mc._serializer is None
        assert mc._kwargs == {"namespace": "test"}

    def test_fails_at_instantiation(self):
        with pytest.raises(TypeError):

            @multi_cached(wrong_param=1)
            async def fn(n):
                return n

    def test_alias_takes_precedence(self, mock_cache):
        with patch(
            "aiocache.decorators.caches.get", MagicMock(return_value=mock_cache)
        ) as mock_get:
            mc = multi_cached(
                keys_from_attr="keys", alias="default", cache=SimpleMemoryCache, namespace="test"
            )
            mc(stub_dict)

            mock_get.assert_called_with("default")
            assert mc.cache is mock_cache

    def test_get_cache_keys(self, decorator):
        keys = decorator.get_cache_keys(stub_dict, (), {"keys": ["a", "b"]})
        assert keys == (["a", "b"], [], -1)

    def test_get_cache_keys_empty_list(self, decorator):
        assert decorator.get_cache_keys(stub_dict, (), {"keys": []}) == ([], [], -1)

    def test_get_cache_keys_missing_kwarg(self, decorator):
        assert decorator.get_cache_keys(stub_dict, (), {}) == ([], [], -1)

    def test_get_cache_keys_arg_key_from_attr(self, decorator):
        def fake(keys, a=1, b=2):
            pass

        assert decorator.get_cache_keys(fake, (["a"]), {}) == (["a"], [["a"]], 0)

    def test_get_cache_keys_with_none(self, decorator):
        assert decorator.get_cache_keys(stub_dict, (), {"keys": None}) == ([], [], -1)

    def test_get_cache_keys_with_key_builder(self, decorator):
        decorator.key_builder = lambda key, *args, **kwargs: kwargs["market"] + "_" + key.upper()
        assert decorator.get_cache_keys(stub_dict, (), {"keys": ["a", "b"], "market": "ES"}) == (
            ["ES_A", "ES_B"],
            [],
            -1,
        )

    @pytest.mark.asyncio
    async def test_get_from_cache(self, decorator, decorator_call):
        decorator.cache.multi_get = AsyncMock(return_value=[1, 2, 3])

        assert await decorator.get_from_cache("a", "b", "c") == [1, 2, 3]
        decorator.cache.multi_get.assert_called_with(("a", "b", "c"))

    @pytest.mark.asyncio
    async def test_get_from_cache_no_keys(self, decorator, decorator_call):
        assert await decorator.get_from_cache() == []
        assert decorator.cache.multi_get.call_count == 0

    @pytest.mark.asyncio
    async def test_get_from_cache_exception(self, decorator, decorator_call):
        decorator.cache.multi_get = AsyncMock(side_effect=Exception)

        assert await decorator.get_from_cache("a", "b", "c") == [None, None, None]
        decorator.cache.multi_get.assert_called_with(("a", "b", "c"))

    @pytest.mark.asyncio
    async def test_get_from_cache_conn(self, decorator, decorator_call):
        decorator._conn._conn = AsyncMock()
        decorator.cache.multi_get = AsyncMock(return_value=[1, 2, 3])

        assert await decorator.get_from_cache("a", "b", "c") == [1, 2, 3]
        decorator.cache.multi_get.assert_called_with(("a", "b", "c"))

    @pytest.mark.asyncio
    async def test_calls_no_keys(self, decorator, decorator_call):
        await decorator_call(keys=[])
        assert decorator.cache.multi_get.call_count == 0
        assert stub_dict.call_count == 1

    @pytest.mark.asyncio
    async def test_returns_from_multi_set(self, mocker, decorator, decorator_call):
        mocker.spy(decorator, "get_from_cache")
        mocker.spy(decorator, "set_in_cache")
        decorator.cache.multi_get = AsyncMock(return_value=[1, 2])

        assert await decorator_call(1, keys=["a", "b"]) == {"a": 1, "b": 2}
        decorator.get_from_cache.assert_called_once_with("a", "b")
        assert decorator.set_in_cache.call_count == 0
        assert stub_dict.call_count == 0

    @pytest.mark.asyncio
    async def test_calls_fn_multi_set_when_multi_get_none(self, mocker, decorator, decorator_call):
        mocker.spy(decorator, "get_from_cache")
        mocker.spy(decorator, "set_in_cache")
        decorator.cache.multi_get = AsyncMock(return_value=[None, None])

        ret = await decorator_call(1, keys=["a", "b"], value="value")

        decorator.get_from_cache.assert_called_once_with("a", "b")
        decorator.set_in_cache.assert_called_with(ret, stub_dict, ANY, ANY)
        stub_dict.assert_called_once_with(1, keys=["a", "b"], value="value")

    @pytest.mark.asyncio
    async def test_cache_write_waits_for_future(self, decorator, decorator_call):
        decorator.get_from_cache = AsyncMock(return_value=[None, None])
        decorator.set_in_cache = AsyncMock()
        await decorator_call(1, keys=["a", "b"], value="value")

        decorator.set_in_cache.assert_awaited()

    @pytest.mark.asyncio
    async def test_cache_write_doesnt_wait_for_future(self, decorator, decorator_call):
        decorator.get_from_cache = AsyncMock(return_value=[None, None])
        decorator.set_in_cache = AsyncMock()

        with patch("aiocache.decorators.asyncio.ensure_future"):
            await decorator_call(1, keys=["a", "b"], value="value", aiocache_wait_for_write=False)

        decorator.set_in_cache.assert_not_awaited()
        decorator.set_in_cache.assert_called_once_with({"a": ANY, "b": ANY}, stub_dict, ANY, ANY)

    @pytest.mark.asyncio
    async def test_calls_fn_with_only_missing_keys(self, mocker, decorator, decorator_call):
        mocker.spy(decorator, "set_in_cache")
        decorator.cache.multi_get = AsyncMock(return_value=[1, None])

        assert await decorator_call(1, keys=["a", "b"], value="value") == {"a": ANY, "b": ANY}

        decorator.set_in_cache.assert_called_once_with({"a": ANY, "b": ANY}, stub_dict, ANY, ANY)
        stub_dict.assert_called_once_with(1, keys=["b"], value="value")

    @pytest.mark.asyncio
    async def test_calls_fn_raises_exception(self, mocker, decorator, decorator_call):
        decorator.cache.multi_get = AsyncMock(return_value=[None])
        stub_dict.side_effect = Exception()
        with pytest.raises(Exception):
            assert await decorator_call(keys=[])

    @pytest.mark.asyncio
    async def test_cache_read_disabled(self, decorator, decorator_call):
        await decorator_call(1, keys=["a", "b"], cache_read=False)

        assert decorator.cache.multi_get.call_count == 0
        assert decorator.cache.multi_set.call_count == 1
        assert stub_dict.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_write_disabled(self, decorator, decorator_call):
        decorator.cache.multi_get = AsyncMock(return_value=[None, None])

        await decorator_call(1, keys=["a", "b"], cache_write=False)

        assert decorator.cache.multi_get.call_count == 1
        assert decorator.cache.multi_set.call_count == 0
        assert stub_dict.call_count == 1

    @pytest.mark.asyncio
    async def test_disable_params_not_propagated(self, decorator, decorator_call):
        decorator.cache.multi_get = AsyncMock(return_value=[None, None])

        await decorator_call(1, keys=["a", "b"], cache_read=False, cache_write=False)

        stub_dict.assert_called_once_with(1, keys=["a", "b"])

    @pytest.mark.asyncio
    async def test_set_in_cache(self, decorator, decorator_call):
        await decorator.set_in_cache({"a": 1, "b": 2}, stub_dict, (), {})

        call_args = decorator.cache.multi_set.call_args[0][0]
        assert ("a", 1) in call_args
        assert ("b", 2) in call_args
        assert decorator.cache.multi_set.call_args[1]["ttl"] is SENTINEL

    @pytest.mark.asyncio
    async def test_set_in_cache_with_ttl(self, decorator, decorator_call):
        decorator.ttl = 10
        await decorator.set_in_cache({"a": 1, "b": 2}, stub_dict, (), {})

        assert decorator.cache.multi_set.call_args[1]["ttl"] == decorator.ttl

    @pytest.mark.asyncio
    async def test_set_in_cache_exception(self, decorator, decorator_call):
        decorator.cache.multi_set = AsyncMock(side_effect=Exception)

        assert await decorator.set_in_cache({"a": 1, "b": 2}, stub_dict, (), {}) is None

    @pytest.mark.asyncio
    async def test_decorate(self, mock_cache):
        mock_cache.multi_get = AsyncMock(return_value=[None])
        with patch("aiocache.decorators._get_cache", return_value=mock_cache):

            @multi_cached(keys_from_attr="keys")
            async def fn(keys=None):
                return {"test": 1}

            assert await fn(keys=["test"]) == {"test": 1}
            assert await fn(["test"]) == {"test": 1}
            assert fn.cache == mock_cache

    @pytest.mark.asyncio
    async def test_keeps_signature(self):
        @multi_cached(keys_from_attr="keys")
        async def what(self, keys=None, what=1):
            return "1"

        assert what.__name__ == "what"
        assert str(inspect.signature(what)) == "(self, keys=None, what=1)"
        assert inspect.getfullargspec(what.__wrapped__).args == ["self", "keys", "what"]

    @pytest.mark.asyncio
    async def test_reuses_cache_instance(self):
        with patch("aiocache.decorators._get_cache") as get_c:
            cache = MagicMock(spec=BaseCache)
            cache.multi_get.return_value = [None]
            get_c.side_effect = [cache, None]

            @multi_cached("keys")
            async def what(keys=None):
                return {}

            await what(keys=["a"])
            await what(keys=["a"])

            assert get_c.call_count == 1
            assert cache.multi_get.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_per_function(self):
        @multi_cached("keys")
        async def foo():
            pass

        @multi_cached("keys")
        async def bar():
            pass

        assert foo.cache != bar.cache


def test_get_args_dict():
    def fn(a, b, *args, keys=None, **kwargs):
        pass

    args_dict = _get_args_dict(fn, ("a", "b", "c", "d"), {"what": "what"})
    assert args_dict == {"a": "a", "b": "b", "keys": None, "what": "what"}
