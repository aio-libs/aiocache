import asyncio

from .base import BaseCache


class SimpleMemoryCache(BaseCache):
    """
    Simple cache implemented in local memory. Although all methods could be synchronous
    they are forced to be async in order to keep the same interface with the other backends
    """

    _cache = {}

    def __init__(self, namespace=None, serializer=None):
        self.serializer = serializer or self.get_serializer()
        self.namespace = namespace or ""

    async def get(self, key, default=None, loads_fn=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param default: obj to return when key is not found
        :param loads_fn: callable alternative to use as loads function
        :returns: obj loadsd
        """

        loads = loads_fn or self.serializer.loads
        return loads(SimpleMemoryCache._cache.get(self._build_key(key), default))

    async def multi_get(self, keys, loads_fn=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param loads_fn: callable alternative to use as loads function
        :returns: obj loadsd
        """
        loads = loads_fn or self.serializer.loads
        return [loads(SimpleMemoryCache._cache.get(self._build_key(key))) for key in keys]

    async def set(self, key, value, ttl=None, dumps_fn=None):
        """
        Stores the value in the given key with ttl if specified

        :param key: str
        :param value: obj
        :param ttl: int the expiration time in seconds
        :param dumps_fn: callable alternative to use as dumps function
        :returns:
        """
        dumps = dumps_fn or self.serializer.dumps
        SimpleMemoryCache._cache[self._build_key(key)] = dumps(value)
        if ttl:
            loop = asyncio.get_event_loop()
            loop.call_later(ttl, self._delete, key)
        return True

    async def multi_set(self, pairs, dumps_fn=None):
        """
        Stores multiple values in the given keys.

        :param pairs: list of two element iterables. First is key and second is value
        :param dumps_fn: callable alternative to use as dumps function
        :returns:
        """
        dumps = dumps_fn or self.serializer.dumps

        for key, value in pairs:
            SimpleMemoryCache._cache[self._build_key(key)] = dumps(value)
        return True

    async def delete(self, key):
        """
        Deletes the given key.

        :param key: Key to be deleted
        :returns: int number of deleted keys
        """
        return self._delete(key)

    def _delete(self, key):
        return SimpleMemoryCache._cache.pop(self._build_key(key), 0)
