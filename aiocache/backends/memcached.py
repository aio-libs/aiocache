import asyncio
import aiomcache

from .base import BaseCache


class MemcachedCache(BaseCache):

    def __init__(self, *args, endpoint=None, port=None, loop=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = endpoint or "127.0.0.1"
        self.port = port or 11211
        self._loop = loop or asyncio.get_event_loop()
        self.client = aiomcache.Client(self.endpoint, self.port, loop=self._loop)

    @property
    def _encoding(self):
        return getattr(self.serializer, "encoding", "utf-8")

    async def get(self, key, default=None, loads_fn=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param default: obj to return when key is not found
        :param loads_fn: callable alternative to use as loads function
        :returns: obj deserialized
        """

        loads = loads_fn or self.serializer.loads
        ns_key = self._build_key(key)

        await self.policy.pre_get(key)

        value = await self.client.get(ns_key)

        if value:
            if isinstance(value, bytes) and self._encoding:
                value = bytes.decode(value)
            await self.policy.post_get(key)

        return loads(value) or default

    async def multi_get(self, keys, loads_fn=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param loads_fn: callable alternative to use as loads function
        :returns: obj deserialized
        """
        loads = loads_fn or self.serializer.loads

        for key in keys:
            await self.policy.pre_get(key)

        ns_keys = [self._build_key(key) for key in keys]
        values = [obj for obj in await self.client.multi_get(*ns_keys)]

        decoded_values = []
        for value in values:
            if value is not None and isinstance(value, bytes) and self._encoding:
                decoded_values.append(loads(bytes.decode(value)))
            else:
                decoded_values.append(loads(value))

        for key in keys:
            await self.policy.post_get(key)

        return decoded_values

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

        s_value = dumps(value)
        s_value = str.encode(s_value) if not isinstance(s_value, bytes) else s_value
        ret = await self.client.set(ns_key, s_value, exptime=ttl)

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
            await self.client.set(self._build_key(key), str.encode(dumps(value)))
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
        ttl = ttl or 0
        ns_key = self._build_key(key)

        await self.policy.pre_set(key, value)

        s_value = dumps(value)
        s_value = str.encode(s_value) if not isinstance(s_value, bytes) else s_value
        ret = await self.client.add(ns_key, s_value, exptime=ttl)
        if not ret:
            raise ValueError(
                "Key {} already exists, use .set to update the value".format(ns_key))

        await self.policy.post_set(key, value)
        return ret

    async def delete(self, key):
        """
        Deletes the given key.

        :param key: Key to be deleted
        :returns: int number of deleted keys
        """
        return 1 if await self.client.delete(self._build_key(key)) else 0

    async def exists(self, key):
        """
        Check key exists in the cache.

        :param key: str key to check
        :returns: True if key exists otherwise False
        """
        return await self.client.append(self._build_key(key), b'')

    async def raw(self, command, *args, **kwargs):
        """
        Executes a raw command using the underlying client of memcached. It's under
        the developer responsibility to send the needed args and kwargs.

        :param command: str command to execute
        """
        return await getattr(self.client, command)(*args, **kwargs)

    def _build_key(self, key):
        ns_key = super()._build_key(key)
        return str.encode(ns_key)
