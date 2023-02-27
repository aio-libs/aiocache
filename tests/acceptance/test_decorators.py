import asyncio
import random
from unittest import mock

import pytest

from aiocache import cached, cached_stampede, multi_cached
from ..utils import Keys, ensure_key


async def return_dict(keys=None):
    ret = {}
    for value, key in enumerate(keys or [Keys.KEY, Keys.KEY_1]):
        ret[key] = str(value)
    return ret


async def stub(arg: float, seconds: int = 0) -> str:
    await asyncio.sleep(seconds)
    return str(random.randint(1, 50))


class TestCached:
    @pytest.fixture(autouse=True)
    def default_cache(self, mocker, cache):
        mocker.patch("aiocache.decorators._get_cache", autospec=True, return_value=cache)

    async def test_cached_ttl(self, cache):
        @cached(ttl=2, key_builder=lambda *args, **kw: Keys.KEY)
        async def fn():
            return str(random.randint(1, 50))

        resp1 = await fn()
        resp2 = await fn()

        assert await cache.get(Keys.KEY) == resp1 == resp2
        await asyncio.sleep(2.1)
        assert await cache.get(Keys.KEY) is None

    async def test_cached_key_builder(self, cache):
        def build_key(f, self, a, b):
            return "{}_{}_{}_{}".format(self, f.__name__, a, b)

        @cached(key_builder=build_key)
        async def fn(self, a, b=2):
            return "1"

        await fn("self", 1, 3)
        assert await cache.exists(build_key(fn, "self", 1, 3)) is True

    @pytest.mark.parametrize("decorator", (cached, cached_stampede))
    async def test_cached_skip_cache_func(self, cache, decorator):
        @decorator(skip_cache_func=lambda r: r is None)
        async def sk_func(x):
            return x if x > 0 else None

        arg = 1
        res = await sk_func(arg)
        assert res

        key = decorator().get_cache_key(sk_func, args=(1,), kwargs={})

        assert key
        assert await cache.exists(key)
        assert await cache.get(key) == res

        arg = -1

        await sk_func(arg)

        key = decorator().get_cache_key(sk_func, args=(-1,), kwargs={})

        assert key
        assert not await cache.exists(key)

    async def test_cached_without_namespace(self, cache):
        """Default cache key is created when no namespace is provided"""
        @cached(namespace=None)
        async def fn():
            return "1"

        await fn()
        decorator = cached(namespace=None)
        key = decorator.get_cache_key(fn, args=(), kwargs={})
        assert await cache.exists(key, namespace=None) is True

    async def test_cached_with_namespace(self, cache):
        """Cache key is prefixed with provided namespace"""
        key_prefix = "test"

        @cached(namespace=key_prefix)
        async def ns_fn():
            return "1"

        await ns_fn()
        decorator = cached(namespace=key_prefix)
        key = decorator.get_cache_key(ns_fn, args=(), kwargs={})
        assert await cache.exists(key, namespace=key_prefix) is True


class TestCachedStampede:
    @pytest.fixture(autouse=True)
    def default_cache(self, mocker, cache):
        mocker.patch("aiocache.decorators._get_cache", autospec=True, return_value=cache)

    async def test_cached_stampede(self, mocker, cache):
        mocker.spy(cache, "get")
        mocker.spy(cache, "set")
        decorator = cached_stampede(ttl=10, lease=3)

        await asyncio.gather(decorator(stub)(0.5), decorator(stub)(0.5))

        cache.get.assert_called_with("tests.acceptance.test_decoratorsstub(0.5,)[]")
        assert cache.get.call_count == 4
        cache.set.assert_called_with("tests.acceptance.test_decoratorsstub(0.5,)[]",
                                     mock.ANY, ttl=10)
        assert cache.set.call_count == 1, cache.set.call_args_list

    async def test_locking_dogpile_lease_expiration(self, mocker, cache):
        mocker.spy(cache, "get")
        mocker.spy(cache, "set")
        decorator = cached_stampede(ttl=10, lease=3)

        await asyncio.gather(
            decorator(stub)(1, seconds=1),
            decorator(stub)(1, seconds=2),
            decorator(stub)(1, seconds=3),
        )

        assert cache.get.call_count == 6
        assert cache.set.call_count == 3

    async def test_locking_dogpile_task_cancellation(self, cache):
        @cached_stampede()
        async def cancel_task():
            raise asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await cancel_task()


class TestMultiCachedDecorator:
    @pytest.fixture(autouse=True)
    def default_cache(self, mocker, cache):
        mocker.patch("aiocache.decorators._get_cache", autospec=True, return_value=cache)

    async def test_multi_cached(self, cache):
        multi_cached_decorator = multi_cached("keys")

        default_keys = {Keys.KEY, Keys.KEY_1}
        await multi_cached_decorator(return_dict)(keys=default_keys)

        for key in default_keys:
            assert await cache.get(key) is not None

    async def test_keys_without_kwarg(self, cache):
        @multi_cached("keys")
        async def fn(keys):
            return {Keys.KEY: 1}

        await fn([Keys.KEY])
        assert await cache.exists(Keys.KEY) is True

    async def test_multi_cached_key_builder(self, cache):
        def build_key(key, f, self, keys, market="ES"):
            return "{}_{}_{}".format(f.__name__, ensure_key(key), market)

        @multi_cached(keys_from_attr="keys", key_builder=build_key)
        async def fn(self, keys, market="ES"):
            return {Keys.KEY: 1, Keys.KEY_1: 2}

        await fn("self", keys=[Keys.KEY, Keys.KEY_1])
        assert await cache.exists("fn_" + ensure_key(Keys.KEY) + "_ES") is True
        assert await cache.exists("fn_" + ensure_key(Keys.KEY_1) + "_ES") is True

    async def test_multi_cached_skip_keys(self, cache):
        @multi_cached(keys_from_attr="keys", skip_cache_func=lambda _, v: v is None)
        async def multi_sk_fn(keys, values):
            return {k: v for k, v in zip(keys, values)}

        res = await multi_sk_fn(keys=[Keys.KEY, Keys.KEY_1], values=[42, None])
        assert res
        assert Keys.KEY in res and Keys.KEY_1 in res

        assert await cache.exists(Keys.KEY)
        assert await cache.get(Keys.KEY) == res[Keys.KEY]
        assert not await cache.exists(Keys.KEY_1)

    async def test_fn_with_args(self, cache):
        @multi_cached("keys")
        async def fn(keys, *args):
            assert len(args) == 1
            return {Keys.KEY: 1}

        await fn([Keys.KEY], "arg")
        assert await cache.exists(Keys.KEY) is True

    async def test_double_decorator(self, cache):
        def dummy_d(fn):
            async def wrapper(*args, **kwargs):
                await fn(*args, **kwargs)

            return wrapper

        @dummy_d
        @multi_cached("keys")
        async def fn(keys):
            return {Keys.KEY: 1}

        await fn([Keys.KEY])
        assert await cache.exists(Keys.KEY) is True
