import asyncio
import aiomcache

import aiocache


class MemcachedBackend:

    DEFAULT_ENDPOINT = "127.0.0.1"
    DEFAULT_PORT = 11211

    def __init__(self, endpoint=None, port=None, loop=None, **kwargs):
        super().__init__(**kwargs)
        if issubclass(aiocache.settings.DEFAULT_CACHE, self.__class__):
            self._from_defaults(endpoint, port)
        else:
            self.endpoint = endpoint or self.DEFAULT_ENDPOINT
            self.port = port or self.DEFAULT_PORT
        self._loop = loop or asyncio.get_event_loop()
        self.client = aiomcache.Client(self.endpoint, self.port, loop=self._loop)
        self.encoding = "utf-8"

    def _from_defaults(self, endpoint, port):
        self.endpoint = endpoint or \
            aiocache.settings.DEFAULT_CACHE_KWARGS.get("endpoint", self.DEFAULT_ENDPOINT)
        self.port = port or aiocache.settings.DEFAULT_CACHE_KWARGS.get("port", self.DEFAULT_PORT)

    async def _get(self, key):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :returns: obj in key if found else None
        """
        value = await self.client.get(key)
        if value is not None and self.encoding is not None:
            return bytes.decode(value)
        return value

    async def _multi_get(self, keys):
        """
        Get multi values from the cache. For each key not found it returns a None

        :param key: str
        :returns: list of obj for each key found, else if not found
        """
        values = []
        for value in await self.client.multi_get(*keys):
            if value is not None and self.encoding is not None:
                values.append(bytes.decode(value))
            else:
                values.append(None)
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
        for key, value in pairs:
            value = str.encode(value) if isinstance(value, str) else value
            await self.client.set(key, value, exptime=ttl or 0)

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
        ret = await self.client.add(key, str.encode(value), exptime=ttl or 0)
        if not ret:
            raise ValueError(
                "Key {} already exists, use .set to update the value".format(key))

        return ret

    async def _exists(self, key):
        """
        Check key exists in the cache.

        :param key: str key to check
        :returns: True if key exists otherwise False
        """
        return await self.client.append(key, b'')

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

    async def _raw(self, command, *args, **kwargs):
        """
        Executes a raw command using the underlying client of memcached. It's under
        the developer responsibility to send the needed args and kwargs.

        :param command: str command to execute
        """
        return await getattr(self.client, command)(*args, **kwargs)
