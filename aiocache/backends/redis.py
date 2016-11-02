import asyncio
import itertools
import aioredis


class RedisBackend:

    def __init__(self, endpoint=None, port=None, loop=None):
        self.endpoint = endpoint or "127.0.0.1"
        self.port = port or 6379
        self._pool = None
        self._loop = loop or asyncio.get_event_loop()
        self.encoding = "utf-8"

    async def get(self, key):
        """
        Get a value from the cache

        :param key: str
        :returns: obj in key if found else None
        """

        with await self._connect() as redis:
            return await redis.get(key, encoding=self.encoding)

    async def multi_get(self, keys):
        """
        Get multi values from the cache. For each key not found it returns a None

        :param key: str
        :returns: list of obj for each key found, else if not found
        """
        with await self._connect() as redis:
            return await redis.mget(*keys, encoding=self.encoding)

    async def set(self, key, value, ttl=None):
        """
        Stores the value in the given key.

        :param key: str
        :param value: obj
        :param ttl: int
        :returns: True
        """
        with await self._connect() as redis:
            return await redis.set(key, value, expire=ttl)

    async def multi_set(self, pairs, ttl=None):
        """
        Stores multiple values in the given keys.

        :param pairs: list of two element iterables. First is key and second is value
        :param ttl: int
        :returns: True
        """
        ttl = ttl or 0

        with await self._connect() as redis:
            transaction = redis.multi_exec()
            flattened = list(itertools.chain.from_iterable(
                (key, value) for key, value in pairs))
            transaction.mset(*flattened)
            if ttl > 0:
                for key in flattened[::2]:
                    transaction.expire(key, timeout=ttl)

            await transaction.execute()

        return True

    async def add(self, key, value, ttl=None):
        """
        Stores the value in the given key. Raises an error if the
        key already exists.

        :param key: str
        :param value: obj
        :param ttl: int
        :returns: True if key is inserted
        :raises: Value error if key already exists
        """

        with await self._connect() as redis:
            if await redis.exists(key):
                raise ValueError(
                    "Key {} already exists, use .set to update the value".format(key))
            return await redis.set(key, value, expire=ttl)

    async def exists(self, key):
        """
        Check key exists in the cache.

        :param key: str key to check
        :returns: True if key exists otherwise False
        """
        with await self._connect() as redis:
            exists = await redis.exists(key)
            return True if exists > 0 else False

    async def delete(self, key):
        """
        Deletes the given key.

        :param key: Key to be deleted
        :returns: int number of deleted keys
        """
        with await self._connect() as redis:
            return await redis.delete(key)

    async def raw(self, command, *args, **kwargs):
        """
        Executes a raw command using the underlying client of aioredis. It's under
        the developer responsibility to send the needed args and kwargs.

        :param command: str command to execute
        """
        with await self._connect() as redis:
            return await getattr(redis, command)(*args, **kwargs)

    async def _connect(self):
        if self._pool is None:
            self._pool = await aioredis.create_pool(
                (self.endpoint, self.port), loop=self._loop)

        return await self._pool
