import asyncio
import aioredis

from .base import BaseCache


class RedisCache(BaseCache):

    def __init__(self, endpoint=None, port=None, namespace=None, serializer=None, loop=None):
        self.endpoint = endpoint or "127.0.0.1"
        self.port = port or 6379
        self.serializer = serializer or self.get_serializer()
        self.namespace = namespace or ""
        self.encoding = "utf-8"
        self._pool = None
        self._loop = loop or asyncio.get_event_loop()

    async def get(self, key, default=None, deserialize_fn=None, encoding=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param default: obj to return when key is not found
        :param deserializer_fn: callable alternative to use as deserialize function
        :param encoding: alternative encoding to use. Default is to use the self.serializer.encoding
        :returns: obj deserialized
        """

        deserialize = deserialize_fn or self.serializer.deserialize
        encoding = encoding or getattr(self.serializer, "encoding", self.encoding)

        with await self._connect() as redis:
            return deserialize(
                await redis.get(self._build_key(key), encoding=encoding)) or default

    async def set(self, key, value, ttl=None, serialize_fn=None):
        """
        Stores the value in the given key with ttl if specified

        :param key: str
        :param value: obj
        :param ttl: int the expiration time in seconds
        :param serialize_fn: callable alternative to use as serialize function
        :returns:
        """
        serialize = serialize_fn or self.serializer.serialize
        ttl = ttl or 0

        with await self._connect() as redis:
            return await redis.set(self._build_key(key), serialize(value), expire=ttl)

    async def delete(self, key):
        with await self._connect() as redis:
            return await redis.delete(self._build_key(key))

    async def incr(self, key, count=1):
        with await self._connect() as redis:
            return await redis.incrby(self._build_key(key), count)

    async def ttl(self, key):
        with await self._connect() as redis:
            return await redis.ttl(self._build_key(key))

    async def _connect(self):
        if self._pool is None:
            self._pool = await aioredis.create_pool(
                (self.endpoint, self.port), loop=self._loop)

        return await self._pool
