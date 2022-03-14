import asyncio
from typing import Dict

from aiocache.base import BaseCache
from aiocache.serializers import NullSerializer


class SimpleMemoryBackend:
    """
    Wrapper around dict operations to use it as a cache backend
    """

    _cache: Dict[str, object] = {}
    _handlers: Dict[str, asyncio.TimerHandle] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _get(self, key, encoding="utf-8", _conn=None):
        return SimpleMemoryBackend._cache.get(key)

    async def _gets(self, key, encoding="utf-8", _conn=None):
        return await self._get(key, encoding=encoding, _conn=_conn)

    async def _multi_get(self, keys, encoding="utf-8", _conn=None):
        return [SimpleMemoryBackend._cache.get(key) for key in keys]

    async def _set(self, key, value, ttl=None, _cas_token=None, _conn=None):
        if _cas_token is not None and _cas_token != SimpleMemoryBackend._cache.get(key):
            return 0

        if key in SimpleMemoryBackend._handlers:
            SimpleMemoryBackend._handlers[key].cancel()

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
            raise ValueError("Key {} already exists, use .set to update the value".format(key))

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
        if cls._cache.pop(key, None) is not None:
            handle = cls._handlers.pop(key, None)
            if handle:
                handle.cancel()
            return 1

        return 0


class SimpleMemoryCache(SimpleMemoryBackend, BaseCache):
    """
    Memory cache implementation with the following components as defaults:
        - serializer: :class:`aiocache.serializers.NullSerializer`
        - plugins: None

    Config options are:

    :param serializer: obj derived from :class:`aiocache.serializers.BaseSerializer`.
    :param plugins: list of :class:`aiocache.plugins.BasePlugin` derived classes.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend. Default is None.
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.
    """

    NAME = "memory"

    def __init__(self, serializer=None, **kwargs):
        super().__init__(**kwargs)
        self.serializer = serializer or NullSerializer()

    @classmethod
    def parse_uri_path(cls, path):
        return {}
