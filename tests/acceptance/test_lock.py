import asyncio
import pytest

from aiocache._lock import _RedLock


class TestRedisLock:

    @pytest.fixture
    def lock(self, redis_cache):
        return _RedLock(redis_cache, pytest.KEY, 20)

    @pytest.mark.asyncio
    async def test_acquire(self, redis_cache, lock):
        await lock.__aenter__()
        assert await redis_cache.get(pytest.KEY + '-lock') == lock._value

    @pytest.mark.asyncio
    async def test_release_does_nothing_when_no_lock(self, redis_cache, lock):
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 0

    @pytest.mark.asyncio
    async def test_acquire_release(self, redis_cache, lock):
        await lock.__aenter__()
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 1
        assert await redis_cache.get(pytest.KEY + '-lock') is None

    @pytest.mark.asyncio
    async def test_release_wrong_token_fails(self, redis_cache, lock):
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


class TestMemcachedLock:

    @pytest.fixture
    def lock(self, memcached_cache):
        return _RedLock(memcached_cache, pytest.KEY, 20)

    @pytest.mark.asyncio
    async def test_acquire(self, memcached_cache, lock):
        await lock.__aenter__()
        assert await memcached_cache.get(pytest.KEY + '-lock') == lock._value

    @pytest.mark.asyncio
    async def test_release_does_nothing_when_no_lock(self, memcached_cache, lock):
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 0

    @pytest.mark.asyncio
    async def test_acquire_release(self, memcached_cache, lock):
        await lock.__aenter__()
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 1
        assert await memcached_cache.get(pytest.KEY + '-lock') is None

    @pytest.mark.asyncio
    async def test_release_wrong_token_succeeds_meh(self, memcached_cache, lock):
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
