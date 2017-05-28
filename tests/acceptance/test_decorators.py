import asyncio
import sys
import pytest
import random

from unittest import mock

from aiocache import cached, multi_cached


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


class TestCachedDecorator:

    @pytest.fixture(autouse=True)
    def default_cache(self, mocker, cache):
        mocker.patch("aiocache.decorators._get_cache", return_value=cache)

    @pytest.mark.asyncio
    async def test_cached_ttl(self, mocker, cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')
        cached_decorator = cached(ttl=1)

        resp1 = await cached_decorator(stub)(1)
        resp2 = await cached_decorator(stub)(1)

        assert await cache.get('stubstub(1,){}') == resp1 == resp2
        await asyncio.sleep(1)
        assert await cache.get('stubstub(1,){}') is None

    @pytest.mark.asyncio
    async def test_cached_key_from_attr(self, mocker, cache):
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')
        cached_decorator = cached(key_from_attr="key")

        resp1 = await cached_decorator(stub)(key='key')
        resp2 = await cached_decorator(stub)(key='key')

        assert await cache.get('key') == resp1 == resp2

    @pytest.mark.asyncio
    async def test_cached_key(self, mocker, cache):
        cached_decorator = cached(key="key")

        resp1 = await cached_decorator(stub)()
        resp2 = await cached_decorator(stub)()

        assert await cache.get('key') == resp1 == resp2

    @pytest.mark.asyncio
    async def test_cached_stampede(self, mocker, cache):
        mocker.spy(cache, 'get')
        mocker.spy(cache, 'set')
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')
        cached_decorator = cached(ttl=10, stampede_lease=2)

        await asyncio.gather(
            cached_decorator(stub)(1),
            cached_decorator(stub)(1))

        cache.get.assert_called_with('stubstub(1,){}')
        assert cache.get.call_count == 4
        cache.set.assert_called_with('stubstub(1,){}', mock.ANY, ttl=10)
        assert cache.set.call_count == 1

    @pytest.mark.asyncio
    async def test_locking_dogpile_lease_expiration(self, mocker, cache):
        mocker.spy(cache, 'get')
        mocker.spy(cache, 'set')
        module = sys.modules[globals()['__name__']]
        mocker.spy(module, 'stub')
        cached_decorator = cached(ttl=10, stampede_lease=1)

        await asyncio.gather(
            cached_decorator(stub)(1, seconds=2),
            cached_decorator(stub)(1, seconds=2))

        assert cache.get.call_count == 4
        assert cache.set.call_count == 2


class TestMultiCachedDecorator:

    @pytest.fixture(autouse=True)
    def default_cache(self, mocker, cache):
        mocker.patch("aiocache.decorators._get_cache", return_value=cache)

    @pytest.mark.asyncio
    async def test_multi_cached(self, mocker, cache):
        multi_cached_decorator = multi_cached('keys')

        default_keys = {'a', 'd', 'z', 'y'}
        await multi_cached_decorator(return_dict)(keys=default_keys)

        for key in default_keys:
            assert await cache.get(key) is not None
