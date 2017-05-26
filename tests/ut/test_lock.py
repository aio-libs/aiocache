import asyncio
import pytest
import asynctest

from aiocache._lock import _DistributedLock


@pytest.fixture
def lock(mock_cache):
    _DistributedLock._EVENTS = {}
    yield _DistributedLock(mock_cache, pytest.KEY, 20)


class TestLock:

    @pytest.mark.asyncio
    async def test_acquire(self, mock_cache, lock):
        await lock._acquire()
        mock_cache._add.assert_called_with(
            pytest.KEY + '-lock', lock._value, ttl=20)
        assert lock._EVENTS[pytest.KEY + '-lock'].is_set() is False

    @pytest.mark.asyncio
    async def test_release(self, mock_cache, lock):
        await lock._acquire()
        await lock._release()
        mock_cache._redlock_release.assert_called_with(
            pytest.KEY + '-lock',
            lock._value)
        assert pytest.KEY + '-lock' not in lock._EVENTS

    @pytest.mark.asyncio
    async def test_second_release(self, mock_cache, lock):
        await lock._acquire()
        mock_cache._redlock_release.side_effect = [True, False]
        assert pytest.KEY + '-lock' in lock._EVENTS
        assert await lock._release() is True
        assert pytest.KEY + '-lock' not in lock._EVENTS
        assert await lock._release() is False

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_cache, lock):
        async with lock:
            pass
        mock_cache._add.assert_called_with(
            pytest.KEY + '-lock', lock._value, ttl=20)
        mock_cache._redlock_release.assert_called_with(
            pytest.KEY + '-lock',
            lock._value)

    @pytest.mark.asyncio
    async def test_acquire_block_timeouts(self, mock_cache, lock):
        await lock._acquire()
        with asynctest.patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            mock_cache._add.side_effect = ValueError
            assert await lock._acquire() is None

    @pytest.mark.asyncio
    async def test_wait_for_release_no_acquire(self, mock_cache, lock):
        mock_cache._add.side_effect = ValueError
        assert await lock._acquire() is None

    @pytest.mark.asyncio
    async def test_multiple_locks_lock(self, mock_cache, lock, event_loop):
        lock_1 = _DistributedLock(mock_cache, pytest.KEY, 20)
        lock_2 = _DistributedLock(mock_cache, pytest.KEY, 20)
        mock_cache._add.side_effect = [True, ValueError(), ValueError()]
        await lock._acquire()
        event = lock._EVENTS[pytest.KEY + '-lock']

        assert pytest.KEY + '-lock' in lock._EVENTS
        assert pytest.KEY + '-lock' in lock_1._EVENTS
        assert pytest.KEY + '-lock' in lock_2._EVENTS
        assert not event.is_set()

        await asyncio.gather(lock_1._acquire(), lock._release(), lock_2._acquire())

        assert pytest.KEY + '-lock' not in lock._EVENTS
        assert pytest.KEY + '-lock' not in lock_1._EVENTS
        assert pytest.KEY + '-lock' not in lock_2._EVENTS
        assert event.is_set()
