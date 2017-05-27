import asyncio
import uuid


class _RedLock:
    """
    Implementation of [Redlock](https://redis.io/topics/distlock)
    with a single instance because aiocache is focused on single
    instance cache.

    This locking has some limitations and shouldn't be used in **bold**
    situations where consistency is critical. Those locks are aimed for
    performance reasons where failing on locking from time to time
    is acceptable. TLDR: do NOT use this if you need real resource
    exclusion.

    Couple of considerations with the implementation:

        - If the lease expires and there are clients waiting, all of them
          will pass (blocking just happens for the first time).
        - When a new client arrives, it will wait always at most lease
          time. This means that the client could end up blocked longer
          than needed in case the lease from the blocker expires.

    Backend specific implementation:

        - Redis implements correctly the redlock algorithm. It sets
          the key if it doesn't exist. To release, it checks the value
          is the same as the instance trying to release and if it is,
          it removes the lock. If not it will do nothing
        - Memcached follows the same approach with a difference. Due
          to memcached lacking a way to execute the operation get and
          delete commands atomically, any client is able to release the
          lock. This is a limitation that can't be fixed safely.
        - Memory implementation is not distributed, it will only apply
          to the process running. Say you have 4 processes running
          APIs with aiocache, the locking will apply only per process
          (still useful to reduce load per process).
    """

    _EVENTS = {}

    def __init__(self, client, key, lease):
        self.client = client
        self.key = self.client._build_key(key + '-lock')
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
            _RedLock._EVENTS[self.key] = asyncio.Event()
        except ValueError:
            await self._wait_for_release()

    async def _wait_for_release(self):
        try:
            await asyncio.wait_for(
                _RedLock._EVENTS[self.key].wait(),
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
            _RedLock._EVENTS.pop(self.key).set()
        return removed
