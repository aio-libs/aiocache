import asyncio

from aiocache.serializers import DefaultSerializer
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

    def get_serializer(self):
        return DefaultSerializer()

    async def get(self, key, default=None, deserialize_fn=None, encoding=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param default: obj to return when key is not found
        :param deserializer_fn: callable alternative to use as deserialize function
        :returns: obj deserialized
        """

        deserialize = deserialize_fn or self.serializer.deserialize
        return deserialize(SimpleMemoryCache._cache.get(self._build_key(key), default))

    async def set(self, key, value, timeout=None, serialize_fn=None):
        """
        Stores the value in the given key with timeout if specified

        :param key: str
        :param value: obj
        :param timeout: int the expiration time in seconds
        :param serialize_fn: callable alternative to use as serialize function
        :returns:
        """
        serialize = serialize_fn or self.serializer.serialize
        SimpleMemoryCache._cache[self._build_key(key)] = serialize(value)
        if timeout:
            loop = asyncio.get_event_loop()
            loop.call_later(timeout, self._delete, key)

    async def delete(self, key):
        return self._delete(key)

    def _delete(self, key):
        return SimpleMemoryCache._cache.pop(self._build_key(key), None)

    async def incr(self, key, count=1):
        SimpleMemoryCache._cache[self._build_key(key)] = \
            SimpleMemoryCache._cache.get(self._build_key(key), 0) + count
        return SimpleMemoryCache._cache.get(self._build_key(key))
