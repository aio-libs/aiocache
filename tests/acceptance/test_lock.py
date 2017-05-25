import pytest

from aiocache._lock import _DistributedLock


@pytest.fixture
def lock(redis_cache):
    return _DistributedLock(redis_cache, pytest.KEY, 20)


class TestLock:

    @pytest.mark.asyncio
    async def test_acquire(self, redis_cache, lock):
        await lock.__aenter__()
        assert await redis_cache.get(pytest.KEY + '-lock') == lock._value
        await redis_cache.delete(pytest.KEY + '-lock')

    @pytest.mark.asyncio
    async def test_release_does_nothing_when_no_lock(self, redis_cache, lock):
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 0

    @pytest.mark.asyncio
    async def test_release_does_nothing_when_wrong_token(self, redis_cache, lock):
        await lock.__aenter__()
        lock._value = "random"
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 0
        await redis_cache.delete(pytest.KEY + '-lock')

    @pytest.mark.asyncio
    async def test_acquire_release(self, redis_cache, lock):
        await lock.__aenter__()
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") == 1
        assert await redis_cache.get(pytest.KEY + '-lock') is None
