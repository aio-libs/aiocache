import asyncio

from .base import BaseCache


class SimpleMemoryCache(BaseCache):
    """
    Simple cache implemented in local memory. Although all methods could be synchronous
    they are forced to be async in order to keep the same interface with the other backends
    """

    _cache = {}

    async def get(self, key, default=None, loads_fn=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param default: obj to return when key is not found
        :param loads_fn: callable alternative to use as loads function
        :returns: obj loadsd
        """

        loads = loads_fn or self.serializer.loads
        ns_key = self._build_key(key)

        await self.policy.pre_get(key)
        value = loads(SimpleMemoryCache._cache.get(ns_key))

        if value:
            await self.policy.post_get(key)

        return value or default

    async def multi_get(self, keys, loads_fn=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param loads_fn: callable alternative to use as loads function
        :returns: obj loadsd
        """
        loads = loads_fn or self.serializer.loads

        for key in keys:
            await self.policy.pre_get(key)

        values = [loads(SimpleMemoryCache._cache.get(self._build_key(key))) for key in keys]

        for key in keys:
            await self.policy.post_get(key)

        return values

    async def set(self, key, value, ttl=None, dumps_fn=None):
        """
        Stores the value in the given key with ttl if specified

        :param key: str
        :param value: obj
        :param ttl: int the expiration time in seconds
        :param dumps_fn: callable alternative to use as dumps function
        :returns: True
        """
        dumps = dumps_fn or self.serializer.dumps
        ns_key = self._build_key(key)

        await self.policy.pre_set(key, value)
        SimpleMemoryCache._cache[ns_key] = dumps(value)
        if ttl:
            loop = asyncio.get_event_loop()
            loop.call_later(ttl, self._delete, ns_key)

        await self.policy.post_set(key, value)
        return True

    async def multi_set(self, pairs, dumps_fn=None):
        """
        Stores multiple values in the given keys.

        :param pairs: list of two element iterables. First is key and second is value
        :param dumps_fn: callable alternative to use as dumps function
        :returns: True
        """
        dumps = dumps_fn or self.serializer.dumps

        for key, value in pairs:
            await self.policy.pre_set(key, value)
            SimpleMemoryCache._cache[self._build_key(key)] = dumps(value)
            await self.policy.post_set(key, value)
        return True

    async def add(self, key, value, ttl=None, dumps_fn=None):
        """
        Stores the value in the given key with ttl if specified. Raises an error if the
        key already exists.

        :param key: str
        :param value: obj
        :param ttl: int the expiration time in seconds
        :param dumps_fn: callable alternative to use as dumps function
        :returns: True if key is inserted
        :raises: Value error if key already exists
        """
        dumps = dumps_fn or self.serializer.dumps
        ns_key = self._build_key(key)

        if ns_key in SimpleMemoryCache._cache:
            raise ValueError(
                "Key {} already exists, use .set to update the value".format(ns_key))

        await self.policy.pre_set(key, value)
        SimpleMemoryCache._cache[ns_key] = dumps(value)
        if ttl:
            loop = asyncio.get_event_loop()
            loop.call_later(ttl, self._delete, ns_key)
        await self.policy.post_set(key, value)
        return True

    async def exists(self, key):
        """
        Check key exists in the cache.

        :param key: str key to check
        :returns: True if key exists otherwise False
        """
        return self._build_key(key) in SimpleMemoryCache._cache

    async def delete(self, key):
        """
        Deletes the given key.

        :param key: Key to be deleted
        :returns: int number of deleted keys
        """
        key = self._build_key(key)
        return self._delete(key)

    def _delete(self, key):
        return SimpleMemoryCache._cache.pop(key, 0)
