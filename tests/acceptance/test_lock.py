import asyncio
import pytest

from aiocache._lock import _RedLock
from aiocache.serializers import StringSerializer


@pytest.fixture
def lock(cache):
    return _RedLock(cache, pytest.KEY, 20)


class TestRedLock:

    @pytest.mark.asyncio
    async def test_acquire(self, cache, lock):
        await lock.__aenter__()
        cache.serializer = StringSerializer()
        assert await cache.get(pytest.KEY + '-lock') == lock._value

    @pytest.mark.asyncio
    async def test_release_does_nothing_when_no_lock(self, lock):
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 0

    @pytest.mark.asyncio
    async def test_acquire_release(self, cache, lock):
        await lock.__aenter__()
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 1
        assert await cache.get(pytest.KEY + '-lock') is None


class TestMemoryRedLock:

    @pytest.fixture
    def lock(self, memory_cache):
        return _RedLock(memory_cache, pytest.KEY, 20)

    @pytest.mark.asyncio
    async def test_release_wrong_token_fails(self, lock):
        await lock.__aenter__()
        lock._value = "random"
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 0

    @pytest.mark.asyncio
    async def test_release_wrong_client_fails(self, memory_cache, lock):
        wrong_lock = _RedLock(memory_cache, pytest.KEY, 20)
        await lock.__aenter__()
        assert await wrong_lock.__aexit__("exc_type", "exc_value", "traceback") == 0

    @pytest.mark.asyncio
    async def test_float_lease(self, memory_cache):
        lock = _RedLock(memory_cache, pytest.KEY, 0.1)
        await lock.__aenter__()
        await asyncio.sleep(0.2)
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 0


class TestRedisRedLock:

    @pytest.fixture
    def lock(self, redis_cache):
        return _RedLock(redis_cache, pytest.KEY, 20)

    @pytest.mark.asyncio
    async def test_release_wrong_token_fails(self, lock):
        await lock.__aenter__()
        lock._value = "random"
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 0

    @pytest.mark.asyncio
    async def test_release_wrong_client_fails(self, redis_cache, lock):
        wrong_lock = _RedLock(redis_cache, pytest.KEY, 20)
        await lock.__aenter__()
        assert await wrong_lock.__aexit__("exc_type", "exc_value", "traceback") == 0

    @pytest.mark.asyncio
    async def test_float_lease(self, redis_cache):
        lock = _RedLock(redis_cache, pytest.KEY, 0.1)
        await lock.__aenter__()
        await asyncio.sleep(0.2)
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 0


class TestMemcachedRedLock:

    @pytest.fixture
    def lock(self, memcached_cache):
        return _RedLock(memcached_cache, pytest.KEY, 20)

    @pytest.mark.asyncio
    async def test_release_wrong_token_succeeds_meh(self, lock):
        await lock.__aenter__()
        lock._value = "random"
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 1

    @pytest.mark.asyncio
    async def test_release_wrong_client_succeeds_meh(self, memcached_cache, lock):
        wrong_lock = _RedLock(memcached_cache, pytest.KEY, 20)
        await lock.__aenter__()
        assert await wrong_lock.__aexit__("exc_type", "exc_value", "traceback") == 1

    @pytest.mark.asyncio
    async def test_float_lease(self, memcached_cache):
        lock = _RedLock(memcached_cache, pytest.KEY, 0.1)
        with pytest.raises(TypeError):
            await lock.__aenter__()
