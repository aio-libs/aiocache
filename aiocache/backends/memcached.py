import asyncio
import aiomcache

from aiocache.base import BaseCache


class MemcachedBackend:

    def __init__(
            self, endpoint="127.0.0.1", port=11211, pool_size=2,
            loop=None, **kwargs):
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.port = port
        self.pool_size = pool_size
        self._loop = loop
        self.client = aiomcache.Client(
            self.endpoint, self.port, loop=self._loop, pool_size=self.pool_size)

    async def _get(self, key, encoding="utf-8"):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :returns: obj in key if found else None
        """
        value = await self.client.get(key)
        if encoding is None or value is None:
            return value
        return value.decode(encoding)

    async def _multi_get(self, keys, encoding="utf-8"):
        """
        Get multi values from the cache. For each key not found it returns a None

        :param key: str
        :returns: list of obj for each key found, else if not found
        """
        values = []
        for value in await self.client.multi_get(*keys):
            if encoding is None or value is None:
                values.append(value)
            else:
                values.append(value.decode(encoding))
        return values

    async def _set(self, key, value, ttl=0):
        """
        Stores the value in the given key.

        :param key: str
        :param value: obj
        :param ttl: int
        :returns: True
        """
        value = str.encode(value) if isinstance(value, str) else value
        return await self.client.set(key, value, exptime=ttl or 0)

    async def _multi_set(self, pairs, ttl=0):
        """
        Stores multiple values in the given keys.

        :param pairs: list of two element iterables. First is key and second is value
        :param ttl: int
        :returns: True
        """
        tasks = []
        for key, value in pairs:
            value = str.encode(value) if isinstance(value, str) else value
            tasks.append(asyncio.ensure_future(self.client.set(key, value, exptime=ttl or 0)))

        await asyncio.gather(*tasks)

        return True

    async def _add(self, key, value, ttl=0):
        """
        Stores the value in the given key. Raises an error if the
        key already exists.

        :param key: str
        :param value: obj
        :param ttl: int
        :returns: True if key is inserted
        :raises: Value error if key already exists
        """
        value = str.encode(value) if isinstance(value, str) else value
        ret = await self.client.add(key, value, exptime=ttl or 0)
        if not ret:
            raise ValueError(
                "Key {} already exists, use .set to update the value".format(key))

        return True

    async def _exists(self, key):
        """
        Check key exists in the cache.

        :param key: str key to check
        :returns: True if key exists otherwise False
        """
        return await self.client.append(key, b'')

    async def _increment(self, key, delta):
        incremented = None
        try:
            if delta > 0:
                incremented = await self.client.incr(key, delta)
            else:
                incremented = await self.client.decr(key, abs(delta))
        except aiomcache.exceptions.ClientException as e:
            if "NOT_FOUND" in str(e):
                await self._set(key, str(delta).encode())
            else:
                raise TypeError("Value is not an integer") from None

        return incremented or delta

    async def _expire(self, key, ttl):
        """
        Expire the given key in ttl seconds. If ttl is 0, remove the expiration

        :param key: str key to expire
        :param ttl: int number of seconds for expiration. If 0, ttl is disabled
        :returns: True if set, False if key is not found
        """
        return await self.client.touch(key, ttl)

    async def _delete(self, key):
        """
        Deletes the given key.

        :param key: Key to be deleted
        :returns: int number of deleted keys
        """
        return 1 if await self.client.delete(key) else 0

    async def _clear(self, namespace=None):
        """
        Deletes the given key.

        :param namespace:
        :returns: True
        """
        if namespace:
            raise ValueError("MemcachedBackend doesnt support flushing by namespace")
        else:
            await self.client.flush_all()
        return True

    async def _raw(self, command, *args, encoding="utf-8", **kwargs):
        """
        Executes a raw command using the underlying client of memcached. It's under
        the developer responsibility to send the needed args and kwargs.

        :param command: str command to execute
        """
        value = await getattr(self.client, command)(*args, **kwargs)
        if command in ["get", "multi_get"]:
            if encoding is not None and value is not None:
                return value.decode(encoding)
        return value


class MemcachedCache(MemcachedBackend, BaseCache):
    """
    Memcached cache implementation with the following
    components as defaults:
      - serializer: :class:`aiocache.serializers.DefaultSerializer`
      - plugins: []

    Config options are:

    :param serializer: obj derived from :class:`aiocache.serializers.DefaultSerializer`.
    :param plugins: list of :class:`aiocache.plugins.BasePlugin` derived classes.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend. Default is None
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.
    :param endpoint: str with the endpoint to connect to. Default is 127.0.0.1.
    :param port: int with the port to connect to. Default is 11211.
    :param pool_size: int size for memcached connections pool. Default is 2.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _build_key(self, key, namespace=None):
        ns_key = super()._build_key(key, namespace=namespace)
        return str.encode(ns_key)

    def __repr__(self):  # pragma: no cover
        return "MemcachedCache ({}:{})".format(self.endpoint, self.port)
