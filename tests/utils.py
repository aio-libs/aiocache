from enum import Enum
from typing import Optional, Union

from aiocache.base import BaseCache


class Keys(str, Enum):
    KEY: str = "key"
    KEY_1: str = "random"


KEY_LOCK = Keys.KEY + "-lock"


def ensure_key(key: Union[str, Enum]) -> str:
    if isinstance(key, Enum):
        return key.value
    else:
        return key


class AbstractBaseCache(BaseCache[str]):
    """BaseCache that can be mocked for NotImplementedError tests"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def build_key(self, key: str, namespace: Optional[str] = None) -> str:
        return super().build_key(key, namespace)

    async def _add(self, key, value, ttl, _conn=None):
        return await super()._add(key, value, ttl, _conn)

    async def _get(self, key, encoding, _conn=None):
        return await super()._get(key, encoding, _conn)

    async def _gets(self, key, encoding="utf-8", _conn=None):
        return await super()._gets(key, encoding, _conn)

    async def _multi_get(self, keys, encoding, _conn=None):
        return await super()._multi_get(keys, encoding, _conn)

    async def _set(self, key, value, ttl, _cas_token=None, _conn=None):
        return await super()._set(key, value, ttl, _cas_token, _conn)

    async def _multi_set(self, pairs, ttl, _conn=None):
        return await super()._multi_set(pairs, ttl, _conn)

    async def _delete(self, key, _conn=None):
        return await super()._delete(key, _conn)

    async def _exists(self, key, _conn=None):
        return await super()._exists(key, _conn)

    async def _increment(self, key, delta, _conn=None):
        return await super()._increment(key, delta, _conn)

    async def _expire(self, key, ttl, _conn=None):
        return await super()._expire(key, ttl, _conn)

    async def _clear(self, namespace, _conn=None):
        return await super()._clear(namespace, _conn)

    async def _raw(self, command, *args, **kwargs):
        return await super()._raw(command, *args, **kwargs)

    async def _redlock_release(self, key, value):
        return await super()._redlock_release(key, value)


class ConcreteBaseCache(AbstractBaseCache):
    """BaseCache that can be mocked for tests"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def build_key(self, key: str, namespace: Optional[str] = None) -> str:
        return self._str_build_key(key, namespace)
