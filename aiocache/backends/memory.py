import asyncio

from aiocache.base import BaseCache


class SimpleMemoryBackend:
    """
    Wrapper around dict operations to use it as a cache backend
    """

    _cache = {}
    _handlers = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _get(self, key, encoding="utf-8", _conn=None):
        return SimpleMemoryBackend._cache.get(key)

    async def _multi_get(self, keys, encoding="utf-8", _conn=None):
        return [SimpleMemoryBackend._cache.get(key) for key in keys]

    async def _set(self, key, value, ttl=None, _conn=None):
        SimpleMemoryBackend._cache[key] = value
        if ttl:
            loop = asyncio.get_event_loop()
            SimpleMemoryBackend._handlers[key] = loop.call_later(ttl, self.__delete, key)
        return True

    async def _multi_set(self, pairs, ttl=None, _conn=None):
        for key, value in pairs:
            await self._set(key, value, ttl=ttl)
        return True

    async def _add(self, key, value, ttl=None, _conn=None):
        if key in SimpleMemoryBackend._cache:
            raise ValueError(
                "Key {} already exists, use .set to update the value".format(key))

        await self._set(key, value, ttl=ttl)
        return True

    async def _exists(self, key, _conn=None):
        return key in SimpleMemoryBackend._cache

    async def _increment(self, key, delta, _conn=None):
        if key not in SimpleMemoryBackend._cache:
            SimpleMemoryBackend._cache[key] = delta
        else:
            try:
                SimpleMemoryBackend._cache[key] = int(SimpleMemoryBackend._cache[key]) + delta
            except ValueError:
                raise TypeError("Value is not an integer") from None
        return SimpleMemoryBackend._cache[key]

    async def _expire(self, key, ttl, _conn=None):
        if key in SimpleMemoryBackend._cache:
            handle = SimpleMemoryBackend._handlers.pop(key, None)
            if handle:
                handle.cancel()
            if ttl:
                loop = asyncio.get_event_loop()
                SimpleMemoryBackend._handlers[key] = loop.call_later(ttl, self.__delete, key)
            return True

        return False

    async def _delete(self, key, _conn=None):
        return self.__delete(key)

    async def _clear(self, namespace=None, _conn=None):
        if namespace:
            for key in list(SimpleMemoryBackend._cache):
                if key.startswith(namespace):
                    self.__delete(key)
        else:
            SimpleMemoryBackend._cache = {}
            SimpleMemoryBackend._handlers = {}
        return True

    async def _raw(self, command, *args, encoding="utf-8", _conn=None, **kwargs):
        return getattr(SimpleMemoryBackend._cache, command)(*args, **kwargs)

    async def _redlock_release(self, key, value):
        if SimpleMemoryBackend._cache.get(key) == value:
            SimpleMemoryBackend._cache.pop(key)
            return 1
        return 0

    @classmethod
    def __delete(cls, key):
        if cls._cache.pop(key, None):
            handle = cls._handlers.pop(key, None)
            if handle:
                handle.cancel()
            return 1

        return 0


class SimpleMemoryCache(SimpleMemoryBackend, BaseCache):
    """
    Memory cache implementation with the following components as defaults:
        - serializer: :class:`aiocache.serializers.StringSerializer`
        - plugins: None

    Config options are:

    :param serializer: obj derived from :class:`aiocache.serializers.StringSerializer`.
    :param plugins: list of :class:`aiocache.plugins.BasePlugin` derived classes.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend. Default is None.
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
