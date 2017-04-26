import asyncio
import itertools
import aioredis

from aiocache.base import BaseCache


class RedisBackend:

    pools = {}

    def __init__(
            self, endpoint="127.0.0.1", port=6379, db=0, password=None,
            pool_min_size=1, pool_max_size=10, loop=None, **kwargs):
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.port = port
        self.db = db
        self.password = password
        self.pool_min_size = pool_min_size
        self.pool_max_size = pool_max_size
        self._loop = loop or asyncio.get_event_loop()
        self._pool = None

    async def _get(self, key, encoding="utf-8"):
        """
        Get a value from the cache

        :param key: str
        :returns: obj in key if found else None
        """

        with await self._connect() as redis:
            return await redis.get(key, encoding=encoding)

    async def _multi_get(self, keys, encoding="utf-8"):
        """
        Get multi values from the cache. For each key not found it returns a None

        :param key: str
        :returns: list of obj for each key found, else if not found
        """
        with await self._connect() as redis:
            return await redis.mget(*keys, encoding=encoding)

    async def _set(self, key, value, ttl=None):
        """
        Stores the value in the given key.

        :param key: str
        :param value: obj
        :param ttl: int
        :returns: True
        """
        with await self._connect() as redis:
            return await redis.set(key, value, expire=ttl)

    async def _multi_set(self, pairs, ttl=None):
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

    async def _add(self, key, value, ttl=None):
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
            was_set = await redis.set(key, value, expire=ttl, exist=redis.SET_IF_NOT_EXIST)
            if not was_set:
                raise ValueError(
                    "Key {} already exists, use .set to update the value".format(key))
            return was_set

    async def _exists(self, key):
        """
        Check key exists in the cache.

        :param key: str key to check
        :returns: True if key exists otherwise False
        """
        with await self._connect() as redis:
            exists = await redis.exists(key)
            return True if exists > 0 else False

    async def _increment(self, key, delta):
        with await self._connect() as redis:
            try:
                return await redis.incrby(key, delta)
            except aioredis.errors.ReplyError:
                raise TypeError("Value is not an integer") from None

    async def _expire(self, key, ttl):
        """
        Expire the given key in ttl seconds. If ttl is 0, remove the expiration

        :param key: str key to expire
        :param ttl: int number of seconds for expiration. If 0, ttl is disabled
        :returns: True if set, False if key is not found
        """
        with await self._connect() as redis:
            if ttl == 0:
                return await redis.persist(key)
            return await redis.expire(key, ttl)

    async def _delete(self, key):
        """
        Deletes the given key.

        :param key: Key to be deleted
        :returns: int number of deleted keys
        """
        with await self._connect() as redis:
            return await redis.delete(key)

    async def _clear(self, namespace=None):
        """
        Deletes the given key.

        :param namespace:
        :returns: True
        """
        with await self._connect() as redis:
            if namespace:
                keys = await redis.keys("{}:*".format(namespace))
                await redis.delete(*keys)
            else:
                await redis.flushdb()
        return True

    async def _raw(self, command, *args, encoding="utf-8", **kwargs):
        """
        Executes a raw command using the underlying client of aioredis. It's under
        the developer responsibility to send the needed args and kwargs.

        :param command: str command to execute
        """
        if command in ["get", "mget"]:
            kwargs["encoding"] = encoding
        with await self._connect() as redis:
            return await getattr(redis, command)(*args, **kwargs)

    async def _connect(self):
        if self._pool is None:
            self._pool = await aioredis.create_pool(
                (self.endpoint, self.port),
                db=self.db,
                password=self.password,
                loop=self._loop,
                encoding="utf-8",
                minsize=self.pool_min_size,
                maxsize=self.pool_max_size)

        return await self._pool


class RedisCache(RedisBackend, BaseCache):
    """
    Redis cache implementation with the
    following components as defaults:
      - serializer: :class:`aiocache.serializers.DefaultSerializer`
      - plugins: []

    Config options are:

    :param serializer: obj derived from :class:`aiocache.serializers.DefaultSerializer`.
    :param plugins: list of :class:`aiocache.plugins.BasePlugin` derived classes.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend. Default is None.
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.
    :param endpoint: str with the endpoint to connect to. Default is "127.0.0.1".
    :param port: int with the port to connect to. Default is 6379.
    :param db: int indicating database to use. Default is 0.
    :param password: str indicating password to use. Default is None.
    :param pool_min_size: int minimum pool size for the redis connections pool. Default is 1
    :param pool_max_size: int maximum pool size for the redis connections pool. Default is 10
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _build_key(self, key, namespace=None):
        if namespace is not None:
            return "{}{}{}".format(namespace, ":" if namespace else "", key)
        if self.namespace is not None:
            return "{}{}{}".format(self.namespace, ":" if self.namespace else "", key)
        return key

    def __repr__(self):  # pragma: no cover
        return "RedisCache ({}:{})".format(self.endpoint, self.port)
