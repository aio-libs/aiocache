import asyncio
import random
from unittest import mock

import pytest

from aiocache import cached, cached_stampede, multi_cached


async def return_dict(keys=None):
    ret = {}
    for value, key in enumerate(keys or [pytest.KEY, pytest.KEY_1]):
        ret[key] = str(value)
    return ret


async def stub(*args, key=None, seconds=0, **kwargs):
    await asyncio.sleep(seconds)
    if key:
        return str(key)
    return str(random.randint(1, 50))


class TestCached:
    @pytest.fixture(autouse=True)
    def default_cache(self, mocker, cache):
        mocker.patch("aiocache.decorators._get_cache", return_value=cache)

    @pytest.mark.asyncio
    async def test_cached_ttl(self, cache):
        @cached(ttl=1, key=pytest.KEY)
        async def fn():
            return str(random.randint(1, 50))

        resp1 = await fn()
        resp2 = await fn()

        assert await cache.get(pytest.KEY) == resp1 == resp2
        await asyncio.sleep(1)
        assert await cache.get(pytest.KEY) is None

    @pytest.mark.asyncio
    async def test_cached_key_builder(self, cache):
        def build_key(f, self, a, b):
            return "{}_{}_{}_{}".format(self, f.__name__, a, b)

        @cached(key_builder=build_key)
        async def fn(self, a, b=2):
            return "1"

        await fn("self", 1, 3)
        assert await cache.exists(build_key(fn, "self", 1, 3)) is True


class TestCachedStampede:
    @pytest.fixture(autouse=True)
    def default_cache(self, mocker, cache):
        mocker.patch("aiocache.decorators._get_cache", return_value=cache)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="flaky test")
    async def test_cached_stampede(self, mocker, cache):
        mocker.spy(cache, "get")
        mocker.spy(cache, "set")
        decorator = cached_stampede(ttl=10, lease=2)

        await asyncio.gather(decorator(stub)(0.5), decorator(stub)(0.5))

        cache.get.assert_called_with("acceptance.test_decoratorsstub(0.5,)[]")
        assert cache.get.call_count == 4
        cache.set.assert_called_with("acceptance.test_decoratorsstub(0.5,)[]", mock.ANY, ttl=10)
        assert cache.set.call_count == 1

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_locking_dogpile_task_cancellation(self, mocker, cache):
        @cached_stampede()
        async def cancel_task():
            raise asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await cancel_task()


class TestMultiCachedDecorator:
    @pytest.fixture(autouse=True)
    def default_cache(self, mocker, cache):
        mocker.patch("aiocache.decorators._get_cache", return_value=cache)

    @pytest.mark.asyncio
    async def test_multi_cached(self, cache):
        multi_cached_decorator = multi_cached("keys")

        default_keys = {pytest.KEY, pytest.KEY_1}
        await multi_cached_decorator(return_dict)(keys=default_keys)

        for key in default_keys:
            assert await cache.get(key) is not None

    @pytest.mark.asyncio
    async def test_keys_without_kwarg(self, cache):
        @multi_cached("keys")
        async def fn(keys):
            return {pytest.KEY: 1}

        await fn([pytest.KEY])
        assert await cache.exists(pytest.KEY) is True

    @pytest.mark.asyncio
    async def test_multi_cached_key_builder(self, cache):
        def build_key(key, f, self, keys, market="ES"):
            return "{}_{}_{}".format(f.__name__, key, market)

        @multi_cached(keys_from_attr="keys", key_builder=build_key)
        async def fn(self, keys, market="ES"):
            return {pytest.KEY: 1, pytest.KEY_1: 2}

        await fn("self", keys=[pytest.KEY, pytest.KEY_1])
        assert await cache.exists("fn_" + pytest.KEY + "_ES") is True
        assert await cache.exists("fn_" + pytest.KEY_1 + "_ES") is True

    @pytest.mark.asyncio
    async def test_fn_with_args(self, cache):
        @multi_cached("keys")
        async def fn(keys, *args):
            assert len(args) == 1
            return {pytest.KEY: 1}

        await fn([pytest.KEY], "arg")
        assert await cache.exists(pytest.KEY) is True

    @pytest.mark.asyncio
    async def test_double_decorator(self, cache):
        def dummy_d(fn):
            async def wrapper(*args, **kwargs):
                await fn(*args, **kwargs)

            return wrapper

        @dummy_d
        @multi_cached("keys")
        async def fn(keys):
            return {pytest.KEY: 1}

        await fn([pytest.KEY])
        assert await cache.exists(pytest.KEY) is True
