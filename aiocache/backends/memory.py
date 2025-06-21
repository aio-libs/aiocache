import asyncio
import sys
from typing import Any, Iterable, Literal, Union

from aiocache.base import BaseCache, BaseCacheArgs, _Conn
from aiocache.serializers import NullSerializer

if sys.version_info >= (3, 11):
    from typing import Unpack
else:
    from typing_extensions import Unpack  # noqa: I900


class SimpleMemoryCache(BaseCache[str]):
    """
    Memory cache implementation with the following components as defaults:
        - serializer: :class:`aiocache.serializers.NullSerializer`
        - plugins: None
        - backend: dict

    Config options are:

    :param serializer: obj derived from :class:`aiocache.serializers.BaseSerializer`.
    :param plugins: list of :class:`aiocache.plugins.BasePlugin` derived classes.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend. Default is an empty string, "".
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default, its 5.
    """

    NAME = "memory"

    def __init__(self, **kwargs: Unpack[BaseCacheArgs]):
        if "serializer" not in kwargs:
            kwargs["serializer"] = NullSerializer()
        super().__init__(**kwargs)

        self._cache: dict[str, object] = {}
        self._handlers: dict[str, asyncio.TimerHandle] = {}

    async def _get(
        self, key: str, encoding: str = "utf-8", _conn: Union[_Conn, None] = None
    ) -> Union[object, None]:
        return self._cache.get(key)

    async def _gets(
        self, key: str, encoding: str = "utf-8", _conn: Union[_Conn, None] = None
    ) -> Union[object, None]:
        return await self._get(key, encoding=encoding, _conn=_conn)

    async def _multi_get(
        self,
        keys: Iterable[str],
        encoding: str = "utf-8",
        _conn: Union[_Conn, None] = None,
    ) -> Union[object, None]:
        return [self._cache.get(key) for key in keys]

    async def _set(
        self,
        key: str,
        value: object,
        ttl: Union[int, None] = None,
        _cas_token: Union[int, None] = None,
        _conn: Union[_Conn, None] = None,
    ) -> bool:
        if _cas_token is not None and _cas_token != self._cache.get(key):
            return False

        if key in self._handlers:
            self._handlers[key].cancel()

        self._cache[key] = value
        if ttl:
            loop = asyncio.get_running_loop()
            self._handlers[key] = loop.call_later(ttl, self.__delete, key)
        return True

    async def _multi_set(
        self,
        pairs: Iterable[tuple[str, object]],
        ttl: Union[int, None] = None,
        _conn: Union[_Conn, None] = None,
    ) -> bool:
        for key, value in pairs:
            await self._set(key, value, ttl=ttl)
        return True

    async def _add(
        self,
        key: str,
        value: object,
        ttl: Union[int, None] = None,
        _conn: Union[_Conn, None] = None,
    ) -> bool:
        if key in self._cache:
            raise ValueError(
                "Key {} already exists, use .set to update the value".format(key)
            )

        await self._set(key, value, ttl=ttl)
        return True

    async def _exists(self, key: str, _conn: Union[_Conn, None] = None) -> bool:
        return key in self._cache

    async def _increment(
        self, key: str, delta: int, _conn: Union[_Conn, None] = None
    ) -> int:
        if key not in self._cache:
            self._cache[key] = delta
        else:
            try:
                self._cache[key] = int(self._cache[key]) + delta  # type: ignore[call-overload]
            except ValueError:
                raise TypeError("Value is not an integer") from None
        return self._cache[key]  # type: ignore[return-value]

    async def _expire(
        self, key: str, ttl: int, _conn: Union[_Conn, None] = None
    ) -> bool:
        if key in self._cache:
            handle = self._handlers.pop(key, None)
            if handle:
                handle.cancel()
            if ttl:
                loop = asyncio.get_running_loop()
                self._handlers[key] = loop.call_later(ttl, self.__delete, key)
            return True

        return False

    async def _delete(
        self, key: str, _conn: Union[_Conn, None] = None
    ) -> Literal[1, 0]:
        return self.__delete(key)

    async def _clear(
        self, namespace: Union[str, None] = None, _conn: Union[_Conn, None] = None
    ) -> bool:
        if namespace:
            for key in list(self._cache):
                if key.startswith(namespace):
                    self.__delete(key)
        else:
            self._cache = {}
            self._handlers = {}
        return True

    async def _raw(
        self,
        command: str,
        *args: Any,
        encoding: str = "utf-8",
        _conn: Union[_Conn, None] = None,
        **kwargs: Any,
    ) -> Any:
        return getattr(self._cache, command)(*args, **kwargs)

    async def _redlock_release(self, key: str, value: object) -> Literal[1, 0]:
        if self._cache.get(key) == value:
            return self.__delete(key)
        return 0

    def __delete(self, key: str) -> Literal[1, 0]:
        if self._cache.pop(key, None) is not None:
            handle = self._handlers.pop(key, None)
            if handle:
                handle.cancel()
            return 1

        return 0

    def build_key(self, key: str, namespace: Union[str, None] = None) -> str:
        return self._str_build_key(key, namespace)

    @classmethod
    def parse_uri_path(cls, path: str) -> dict[Any, Any]:
        return {}
