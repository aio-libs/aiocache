import asyncio
import uuid


class _DistributedLock:
    """
    Implementation of [Redlock](https://redis.io/topics/distlock)
    with a single instance because aiocache is focused on single
    instance cache.

    Couple of considerations with the implementation:

        - If the lease expires and there are clients waiting, all of them
          will pass (blocking just happens for the first time).
        - When a new client arrives, it will wait always at most lease
          time. This means that the client could end up blocked longer
          than needed in case the lease from the blocker expires.
    """

    _EVENTS = {}

    def __init__(self, client, key, lease):
        self.client = client
        self.key = client._build_key(key + '-lock')
        self.lease = lease
        self._value = ""

    async def __aenter__(self):
        return await self._acquire()

    async def _acquire(self):
        self._value = str(uuid.uuid4())
        try:
            await self.client._add(
                self.key,
                self._value,
                ttl=self.lease)
            _DistributedLock._EVENTS[self.key] = asyncio.Event()
        except ValueError:
            await self._wait_for_release()

    async def _wait_for_release(self):
        try:
            await asyncio.wait_for(
                _DistributedLock._EVENTS[self.key].wait(),
                self.lease)
        except asyncio.TimeoutError:
            pass
        except KeyError:  # lock was released when wait_for was rescheduled
            pass

    async def __aexit__(self, exc_type, exc_value, traceback):
        return await self._release()

    async def _release(self):
        removed = await self.client._redlock_release(self.key, self._value)
        if removed:
            _DistributedLock._EVENTS.pop(self.key).set()
        return removed
