import asyncio
import aioredis

from itertools import chain

from .base import BaseCache


class RedisCache(BaseCache):

    def __init__(self, *args, endpoint=None, port=None, loop=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = endpoint or "127.0.0.1"
        self.port = port or 6379
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
        ns_key = self._build_key(key)

        await self.policy.pre_get(key)

        with await self._connect() as redis:
            value = loads(await redis.get(ns_key, encoding=encoding))

        if value:
            await self.policy.post_get(key)

        return value or default

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

        for key in keys:
            await self.policy.pre_get(key)

        with await self._connect() as redis:
            ns_keys = [self._build_key(key) for key in keys]
            values = [loads(obj) for obj in (await redis.mget(*ns_keys, encoding=encoding))]

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
        ttl = ttl or 0
        ns_key = self._build_key(key)

        await self.policy.pre_set(key, value)

        with await self._connect() as redis:
            ret = await redis.set(ns_key, dumps(value), expire=ttl)

        await self.policy.post_set(key, value)
        return ret

    async def multi_set(self, pairs, dumps_fn=None):
        """
        Stores multiple values in the given keys.

        :param pairs: list of two element iterables. First is key and second is value
        :param dumps: callable alternative to use as dumps function
        :returns: True
        """
        dumps = dumps_fn or self.serializer.dumps

        for key, value in pairs:
            await self.policy.pre_set(key, value)

        with await self._connect() as redis:
            serialized_pairs = list(
                chain.from_iterable(
                    (self._build_key(key), dumps(value)) for key, value in pairs))
            ret = await redis.mset(*serialized_pairs)

        for key, value in pairs:
            await self.policy.post_set(key, value)

        return ret

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
        ns_key = self._build_key(key)

        await self.policy.pre_set(key, value)

        with await self._connect() as redis:
            if await redis.exists(ns_key):
                raise ValueError(
                    "Key {} already exists, use .set to update the value".format(ns_key))
            ret = await redis.set(ns_key, dumps(value), expire=ttl)

        await self.policy.post_set(key, value)
        return ret

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
