import asyncio
from unittest.mock import Mock, patch

import pytest

from aiocache.lock import OptimisticLock, OptimisticLockError, RedLock


class TestRedLock:
    @pytest.fixture
    def lock(self, mock_cache):
        RedLock._EVENTS = {}
        yield RedLock(mock_cache, pytest.KEY, 20)

    @pytest.mark.asyncio
    async def test_acquire(self, mock_cache, lock):
        await lock._acquire()
        mock_cache._add.assert_called_with(pytest.KEY + "-lock", lock._value, ttl=20)
        assert lock._EVENTS[pytest.KEY + "-lock"].is_set() is False

    @pytest.mark.asyncio
    async def test_release(self, mock_cache, lock):
        mock_cache._redlock_release.return_value = True
        await lock._acquire()
        await lock._release()
        mock_cache._redlock_release.assert_called_with(pytest.KEY + "-lock", lock._value)
        assert pytest.KEY + "-lock" not in lock._EVENTS

    @pytest.mark.asyncio
    async def test_release_no_acquire(self, mock_cache, lock):
        mock_cache._redlock_release.return_value = False
        assert pytest.KEY + "-lock" not in lock._EVENTS
        await lock._release()
        assert pytest.KEY + "-lock" not in lock._EVENTS

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_cache, lock):
        async with lock:
            pass
        mock_cache._add.assert_called_with(pytest.KEY + "-lock", lock._value, ttl=20)
        mock_cache._redlock_release.assert_called_with(pytest.KEY + "-lock", lock._value)

    @pytest.mark.asyncio
    async def test_raises_exceptions(self, mock_cache, lock):
        mock_cache._redlock_release.return_value = True
        with pytest.raises(ValueError):
            async with lock:
                raise ValueError

    @pytest.mark.asyncio
    async def test_acquire_block_timeouts(self, mock_cache, lock):
        await lock._acquire()

        # Mock .wait() to avoid unawaited coroutine warning.
        with patch.object(RedLock._EVENTS[lock.key], "wait", Mock()):
            with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
                mock_cache._add.side_effect = ValueError
                assert await lock._acquire() is None

    @pytest.mark.asyncio
    async def test_wait_for_release_no_acquire(self, mock_cache, lock):
        mock_cache._add.side_effect = ValueError
        assert await lock._acquire() is None

    @pytest.mark.asyncio
    async def test_multiple_locks_lock(self, mock_cache, lock):
        lock_1 = RedLock(mock_cache, pytest.KEY, 20)
        lock_2 = RedLock(mock_cache, pytest.KEY, 20)
        mock_cache._add.side_effect = [True, ValueError(), ValueError()]
        await lock._acquire()
        event = lock._EVENTS[pytest.KEY + "-lock"]

        assert pytest.KEY + "-lock" in lock._EVENTS
        assert pytest.KEY + "-lock" in lock_1._EVENTS
        assert pytest.KEY + "-lock" in lock_2._EVENTS
        assert not event.is_set()

        await asyncio.gather(lock_1._acquire(), lock._release(), lock_2._acquire())

        assert pytest.KEY + "-lock" not in lock._EVENTS
        assert pytest.KEY + "-lock" not in lock_1._EVENTS
        assert pytest.KEY + "-lock" not in lock_2._EVENTS
        assert event.is_set()


class TestOptimisticLock:
    @pytest.fixture
    def lock(self, mock_cache):
        yield OptimisticLock(mock_cache, pytest.KEY)

    def test_init(self, mock_cache, lock):
        assert lock.client == mock_cache
        assert lock._token is None
        assert lock.key == pytest.KEY
        assert lock.ns_key == mock_cache._build_key(pytest.KEY)

    @pytest.mark.asyncio
    async def test_aenter_returns_lock(self, lock):
        assert await lock.__aenter__() is lock

    @pytest.mark.asyncio
    async def test_aexit_not_crashing(self, lock):
        async with lock:
            pass

    @pytest.mark.asyncio
    async def test_acquire_calls_get(self, lock):
        await lock._acquire()
        lock.client._gets.assert_called_with(pytest.KEY)
        assert lock._token == lock.client._gets.return_value

    @pytest.mark.asyncio
    async def test_cas_calls_set_with_token(self, lock):
        await lock._acquire()
        await lock.cas("value")
        lock.client.set.assert_called_with(pytest.KEY, "value", _cas_token=lock._token)

    @pytest.mark.asyncio
    async def test_wrong_token_raises_error(self, mock_cache, lock):
        mock_cache._set.return_value = 0
        with pytest.raises(OptimisticLockError):
            await lock.cas("value")
