from abc import ABC, abstractmethod


class BaseBackend(ABC):
    """
    Abstract class for implementation cache backend
    """

    @abstractmethod
    async def _get(self, key, encoding="utf-8", _conn=None):
        pass

    @abstractmethod
    async def _gets(self, key, encoding="utf-8", _conn=None):
        pass

    @abstractmethod
    async def _multi_get(self, keys, encoding="utf-8", _conn=None):
        pass

    @abstractmethod
    async def _set(self, key, value, ttl=None, _cas_token=None, _conn=None):
        pass

    @abstractmethod
    async def _multi_set(self, pairs, ttl=None, _conn=None):
        pass

    @abstractmethod
    async def _add(self, key, value, ttl=None, _conn=None):
        pass

    @abstractmethod
    async def _exists(self, key, _conn=None):
        pass

    @abstractmethod
    async def _increment(self, key, delta, _conn=None):
        pass

    @abstractmethod
    async def _expire(self, key, ttl, _conn=None):
        pass

    @abstractmethod
    async def _delete(self, key, _conn=None):
        pass

    @abstractmethod
    async def _clear(self, namespace=None, _conn=None):
        pass

    @abstractmethod
    async def _raw(self, command, *args, encoding="utf-8", _conn=None, **kwargs):
        pass

    @abstractmethod
    async def _redlock_release(self, key, value):
        pass
