import asyncio
import pytest
import random

from unittest import mock

from aiocache import cached, cached_stampede, multi_cached


async def return_dict(keys=None):
    ret = {}
    for value, key in enumerate(keys or ['a', 'd', 'z', 'y']):
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


class TestCachedStampede:

    @pytest.fixture(autouse=True)
    def default_cache(self, mocker, cache):
        mocker.patch("aiocache.decorators._get_cache", return_value=cache)

    @pytest.mark.asyncio
    async def test_cached_stampede(self, mocker, cache):
        mocker.spy(cache, 'get')
        mocker.spy(cache, 'set')
        decorator = cached_stampede(ttl=10, lease=2)

        await asyncio.gather(
            decorator(stub)(1),
            decorator(stub)(1))

        cache.get.assert_called_with('acceptance.test_decoratorsstub(1,)[]')
        assert cache.get.call_count == 4
        cache.set.assert_called_with('acceptance.test_decoratorsstub(1,)[]', mock.ANY, ttl=10)
        assert cache.set.call_count == 1

    @pytest.mark.asyncio
    async def test_locking_dogpile_lease_expiration(self, mocker, cache):
        mocker.spy(cache, 'get')
        mocker.spy(cache, 'set')
        decorator = cached_stampede(ttl=10, lease=1)

        await asyncio.gather(
            decorator(stub)(1, seconds=2),
            decorator(stub)(1, seconds=2))

        assert cache.get.call_count == 4
        assert cache.set.call_count == 2


class TestMultiCachedDecorator:

    @pytest.fixture(autouse=True)
    def default_cache(self, mocker, cache):
        mocker.patch("aiocache.decorators._get_cache", return_value=cache)

    @pytest.mark.asyncio
    async def test_multi_cached(self, cache):
        multi_cached_decorator = multi_cached('keys')

        default_keys = {'a', 'd', 'z', 'y'}
        await multi_cached_decorator(return_dict)(keys=default_keys)

        for key in default_keys:
            assert await cache.get(key) is not None
