import asyncio
import aioredis

from itertools import chain

from .base import BaseCache


class RedisCache(BaseCache):

    def __init__(self, endpoint=None, port=None, namespace=None, serializer=None, loop=None):
        self.endpoint = endpoint or "127.0.0.1"
        self.port = port or 6379
        self.serializer = serializer or self.get_serializer()
        self.namespace = namespace or ""
        self._pool = None
        self._loop = loop or asyncio.get_event_loop()

    async def get(self, key, default=None, loads_fn=None, encoding=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param default: obj to return when key is not found
        :param loads_fn: callable alternative to use as loads function
        :param encoding: alternative encoding to use. Default is to use the self.serializer.encoding
        :returns: obj deserialized
        """

        loads = loads_fn or self.serializer.loads
        encoding = encoding or getattr(self.serializer, "encoding", 'utf-8')

        with await self._connect() as redis:
            return loads(
                await redis.get(self._build_key(key), encoding=encoding)) or default

    async def multi_get(self, keys, loads_fn=None, encoding=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param loads_fn: callable alternative to use as loads function
        :param encoding: alternative encoding to use. Default is to use the self.serializer.encoding
        :returns: obj deserialized
        """
        loads = loads_fn or self.serializer.loads
        encoding = encoding or getattr(self.serializer, "encoding", 'utf-8')

        with await self._connect() as redis:
            keys = [self._build_key(key) for key in keys]
            return [loads(obj) for obj in (await redis.mget(*keys, encoding=encoding))]

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
        ttl = ttl or 0

        with await self._connect() as redis:
            return await redis.set(self._build_key(key), dumps(value), expire=ttl)

    async def multi_set(self, pairs, dumps_fn=None):
        """
        Stores multiple values in the given keys.

        :param pairs: list of two element iterables. First is key and second is value
        :param dumps: callable alternative to use as dumps function
        :returns: True
        """
        dumps = dumps_fn or self.serializer.dumps

        with await self._connect() as redis:
            serialized_pairs = list(
                chain.from_iterable(
                    (self._build_key(key), dumps(value)) for key, value in pairs))
            return await redis.mset(*serialized_pairs)

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
        ttl = ttl or 0

        key = self._build_key(key)
        with await self._connect() as redis:
            if await redis.exists(key):
                raise ValueError(
                    "Key {} already exists, use .set to update the value".format(key))
            return await redis.set(key, dumps(value), expire=ttl)

    async def exists(self, key):
        """
        Check key exists in the cache.

        :param key: str key to check
        :returns: True if key exists otherwise False
        """
        with await self._connect() as redis:
            return await redis.exists(self._build_key(key))

    async def delete(self, key):
        """
        Deletes the given key.

        :param key: Key to be deleted
        :returns: int number of deleted keys
        """
        with await self._connect() as redis:
            return await redis.delete(self._build_key(key))

    async def ttl(self, key):
        with await self._connect() as redis:
            return await redis.ttl(self._build_key(key))

    async def _connect(self):
        if self._pool is None:
            self._pool = await aioredis.create_pool(
                (self.endpoint, self.port), loop=self._loop)

        return await self._pool
