import asyncio


class SimpleMemoryBackend:
    """
    Wrapper around dict operations to use it as a cache backend
    """

    _cache = {}

    async def get(self, key):
        """
        Get a value from the cache

        :param key: str
        :returns: obj in key if found else None
        """
        return SimpleMemoryBackend._cache.get(key)

    async def multi_get(self, keys):
        """
        Get multi values from the cache. For each key not found it returns a None

        :param key: str
        :returns: list of obj for each key found, else if not found
        """
        return [SimpleMemoryBackend._cache.get(key) for key in keys]

    async def set(self, key, value, ttl=None):
        """
        Stores the value in the given key.

        :param key: str
        :param value: obj
        :param ttl: int
        :returns: True
        """
        SimpleMemoryBackend._cache[key] = value
        if ttl:
            loop = asyncio.get_event_loop()
            loop.call_later(ttl, self._delete, key)
        return True

    async def multi_set(self, pairs, ttl=None):
        """
        Stores multiple values in the given keys.

        :param pairs: list of two element iterables. First is key and second is value
        :param ttl: int
        :returns: True
        """
        for key, value in pairs:
            SimpleMemoryBackend._cache[key] = value
            if ttl:
                loop = asyncio.get_event_loop()
                loop.call_later(ttl, self._delete, key)
        return True

    async def add(self, key, value, ttl=None):
        """
        Stores the value in the given key. Raises an error if the
        key already exists.

        :param key: str
        :param value: obj
        :param ttl: int
        :returns: True if key is inserted
        :raises: Value error if key already exists
        """
        if key in SimpleMemoryBackend._cache:
            raise ValueError(
                "Key {} already exists, use .set to update the value".format(key))

        SimpleMemoryBackend._cache[key] = value
        if ttl:
            loop = asyncio.get_event_loop()
            loop.call_later(ttl, self._delete, key)
        return True

    async def exists(self, key):
        """
        Check key exists in the cache.

        :param key: str key to check
        :returns: True if key exists otherwise False
        """
        return key in SimpleMemoryBackend._cache

    async def delete(self, key):
        """
        Deletes the given key.

        :param key: Key to be deleted
        :returns: int number of deleted keys
        """
        return self._delete(key)

    async def raw(self, command, *args, **kwargs):
        """
        Executes a raw command using the underlying dict structure. It's under
        the developer responsibility to send the needed args and kwargs.

        :param command: str command to execute
        """
        return getattr(SimpleMemoryBackend._cache, command)(*args, **kwargs)

    def _delete(self, key):
        return SimpleMemoryBackend._cache.pop(key, 0)
