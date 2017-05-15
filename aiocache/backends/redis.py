import asyncio
import itertools
import aioredis
import functools

from aiocache.base import BaseCache


def conn(func):
    @functools.wraps(func)
    async def wrapper(self, *args, _conn=None, **kwargs):
        if _conn is None:
            with await self._connect() as _conn:
                return await func(self, *args, _conn=_conn, **kwargs)

        return await func(self, *args, _conn=_conn, **kwargs)
    return wrapper


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
        self._lock = asyncio.Lock()
        self._loop = loop or asyncio.get_event_loop()
        self._pool = None

    async def acquire(self):
        with await self._connect():
            pass
        return await self._pool.acquire()

    async def release(self, conn):
        self._pool.release(conn)

    @conn
    async def _get(self, key, encoding="utf-8", _conn=None):
        """
        Get a value from the cache

        :param key: str
        :returns: obj in key if found else None
        """

        return await _conn.get(key, encoding=encoding)

    @conn
    async def _multi_get(self, keys, encoding="utf-8", _conn=None):
        """
        Get multi values from the cache. For each key not found it returns a None

        :param key: str
        :returns: list of obj for each key found, else if not found
        """
        return await _conn.mget(*keys, encoding=encoding)

    @conn
    async def _set(self, key, value, ttl=None, _conn=None):
        """
        Stores the value in the given key.

        :param key: str
        :param value: obj
        :param ttl: int
        :returns: True
        """
        return await _conn.set(key, value, expire=ttl)

    @conn
    async def _multi_set(self, pairs, ttl=None, _conn=None):
        """
        Stores multiple values in the given keys.

        :param pairs: list of two element iterables. First is key and second is value
        :param ttl: int
        :returns: True
        """
        ttl = ttl or 0

        flattened = list(itertools.chain.from_iterable(
            (key, value) for key, value in pairs))

        if ttl:
            await self.__multi_set_ttl(_conn, flattened, ttl)
        else:
            await _conn.mset(*flattened)

        return True

    async def __multi_set_ttl(self, conn, flattened, ttl):
        redis = conn.multi_exec()
        redis.mset(*flattened)
        for key in flattened[::2]:
            redis.expire(key, timeout=ttl)
        await redis.execute()

    @conn
    async def _add(self, key, value, ttl=None, _conn=None):
        """
        Stores the value in the given key. Raises an error if the
        key already exists.

        :param key: str
        :param value: obj
        :param ttl: int
        :returns: True if key is inserted
        :raises: Value error if key already exists
        """

        was_set = await _conn.set(key, value, expire=ttl, exist=_conn.SET_IF_NOT_EXIST)
        if not was_set:
            raise ValueError(
                "Key {} already exists, use .set to update the value".format(key))
        return was_set

    @conn
    async def _exists(self, key, _conn=None):
        """
        Check key exists in the cache.

        :param key: str key to check
        :returns: True if key exists otherwise False
        """
        exists = await _conn.exists(key)
        return True if exists > 0 else False

    @conn
    async def _increment(self, key, delta, _conn=None):
        try:
            return await _conn.incrby(key, delta)
        except aioredis.errors.ReplyError:
            raise TypeError("Value is not an integer") from None

    @conn
    async def _expire(self, key, ttl, _conn=None):
        """
        Expire the given key in ttl seconds. If ttl is 0, remove the expiration

        :param key: str key to expire
        :param ttl: int number of seconds for expiration. If 0, ttl is disabled
        :returns: True if set, False if key is not found
        """
        if ttl == 0:
            return await _conn.persist(key)
        return await _conn.expire(key, ttl)

    @conn
    async def _delete(self, key, _conn=None):
        """
        Deletes the given key.

        :param key: Key to be deleted
        :returns: int number of deleted keys
        """
        return await _conn.delete(key)

    @conn
    async def _clear(self, namespace=None, _conn=None):
        """
        Deletes the given key.

        :param namespace:
        :returns: True
        """
        if namespace:
            keys = await _conn.keys("{}:*".format(namespace))
            await _conn.delete(*keys)
        else:
            await _conn.flushdb()
        return True

    @conn
    async def _raw(self, command, *args, encoding="utf-8", _conn=None, **kwargs):
        """
        Executes a raw command using the underlying client of aioredis. It's under
        the developer responsibility to send the needed args and kwargs.

        :param command: str command to execute
        """
        if command in ["get", "mget"]:
            kwargs["encoding"] = encoding
        return await getattr(_conn, command)(*args, **kwargs)

    async def _connect(self):
        async with self._lock:
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
