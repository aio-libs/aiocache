import asyncio
from unittest.mock import Mock, patch

import pytest

from aiocache.lock import OptimisticLock, OptimisticLockError, RedLock
from ..utils import KEY_LOCK, Keys


class TestRedLock:
    @pytest.fixture
    def lock(self, mock_base_cache):
        RedLock._EVENTS = {}
        yield RedLock(mock_base_cache, Keys.KEY, 20)

    async def test_acquire(self, mock_base_cache, lock):
        await lock._acquire()
        mock_base_cache._add.assert_called_with(KEY_LOCK, lock._value, ttl=20)
        assert lock._EVENTS[KEY_LOCK].is_set() is False

    async def test_release(self, mock_base_cache, lock):
        mock_base_cache._redlock_release.return_value = True
        await lock._acquire()
        await lock._release()
        mock_base_cache._redlock_release.assert_called_with(KEY_LOCK, lock._value)
        assert KEY_LOCK not in lock._EVENTS

    async def test_release_no_acquire(self, mock_base_cache, lock):
        mock_base_cache._redlock_release.return_value = False
        assert KEY_LOCK not in lock._EVENTS
        await lock._release()
        assert KEY_LOCK not in lock._EVENTS

    async def test_context_manager(self, mock_base_cache, lock):
        async with lock:
            pass
        mock_base_cache._add.assert_called_with(KEY_LOCK, lock._value, ttl=20)
        mock_base_cache._redlock_release.assert_called_with(KEY_LOCK, lock._value)

    async def test_raises_exceptions(self, mock_base_cache, lock):
        mock_base_cache._redlock_release.return_value = True
        with pytest.raises(ValueError):
            async with lock:
                raise ValueError

    async def test_acquire_block_timeouts(self, mock_base_cache, lock):
        await lock._acquire()

        # Mock .wait() to avoid unawaited coroutine warning.
        with patch.object(RedLock._EVENTS[lock.key], "wait", Mock(spec_set=())):
            with patch("asyncio.wait_for", autospec=True, side_effect=asyncio.TimeoutError):
                mock_base_cache._add.side_effect = ValueError
                result = await lock._acquire()
                assert result is None

    async def test_wait_for_release_no_acquire(self, mock_base_cache, lock):
        mock_base_cache._add.side_effect = ValueError
        assert await lock._acquire() is None

    async def test_multiple_locks_lock(self, mock_base_cache, lock):
        lock_1 = RedLock(mock_base_cache, Keys.KEY, 20)
        lock_2 = RedLock(mock_base_cache, Keys.KEY, 20)
        mock_base_cache._add.side_effect = [True, ValueError(), ValueError()]
        await lock._acquire()
        event = lock._EVENTS[KEY_LOCK]

        assert KEY_LOCK in lock._EVENTS
        assert KEY_LOCK in lock_1._EVENTS
        assert KEY_LOCK in lock_2._EVENTS
        assert not event.is_set()

        await asyncio.gather(lock_1._acquire(), lock._release(), lock_2._acquire())

        assert KEY_LOCK not in lock._EVENTS
        assert KEY_LOCK not in lock_1._EVENTS
        assert KEY_LOCK not in lock_2._EVENTS
        assert event.is_set()


class TestOptimisticLock:
    @pytest.fixture
    def lock(self, mock_base_cache):
        yield OptimisticLock(mock_base_cache, Keys.KEY)

    def test_init(self, mock_base_cache, lock):
        assert lock.client == mock_base_cache
        assert lock._token is None
        assert lock.key == Keys.KEY
        assert lock.ns_key == mock_base_cache._build_key(Keys.KEY)

    async def test_aenter_returns_lock(self, lock):
        assert await lock.__aenter__() is lock

    async def test_aexit_not_crashing(self, lock):
        async with lock:
            pass

    async def test_acquire_calls_get(self, lock):
        await lock._acquire()
        lock.client._gets.assert_called_with(Keys.KEY)
        assert lock._token == lock.client._gets.return_value

    async def test_cas_calls_set_with_token(self, lock, mocker):
        m = mocker.spy(lock.client, "set")
        await lock._acquire()
        await lock.cas("value")
        m.assert_called_with(Keys.KEY, "value", _cas_token=lock._token)

    async def test_wrong_token_raises_error(self, mock_base_cache, lock):
        mock_base_cache._set.return_value = 0
        with pytest.raises(OptimisticLockError):
            await lock.cas("value")
