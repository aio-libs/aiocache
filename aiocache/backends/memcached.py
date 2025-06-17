import asyncio
import sys
from typing import Any, Dict, Iterable, List, Literal, Tuple, Union, overload

import aiomcache

from aiocache.base import BaseCache, BaseCacheArgs, _Conn
from aiocache.serializers import JsonSerializer

if sys.version_info >= (3, 11):
    from typing import Unpack
else:
    from typing_extensions import Unpack  # noqa: I900


class MemcachedCache(BaseCache[bytes]):
    """
    Memcached cache implementation with the following components as defaults:
        - serializer: :class:`aiocache.serializers.JsonSerializer`
        - plugins: []

    Config options are:

    :param serializer: obj derived from :class:`aiocache.serializers.BaseSerializer`.
    :param plugins: list of :class:`aiocache.plugins.BasePlugin` derived classes.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend. Default is an empty string, "".
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.
    :param endpoint: str with the endpoint to connect to. Default is 127.0.0.1.
    :param port: int with the port to connect to. Default is 11211.
    :param pool_size: int size for memcached connections pool. Default is 2.
    """

    NAME = "memcached"

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 11211,
        pool_size: int = 2,
        **kwargs: Unpack[BaseCacheArgs],
    ) -> None:
        if "serializer" not in kwargs:
            kwargs["serializer"] = JsonSerializer()
        super().__init__(**kwargs)
        self.host = host
        self.port = port
        self.pool_size = int(pool_size)
        self.client = aiomcache.Client(self.host, self.port, pool_size=self.pool_size)

    @overload
    async def _get(
        self,
        key: bytes,
        encoding: str = "utf-8",
        _conn: Union[_Conn, None] = None,
    ) -> Union[str, None]: ...

    @overload
    async def _get(
        self, key: bytes, encoding: None, _conn: Union[_Conn, None] = None
    ) -> Union[bytes, None]: ...

    async def _get(
        self,
        key: bytes,
        encoding: Union[str, None] = "utf-8",
        _conn: Union[_Conn, None] = None,
    ) -> Union[bytes, str, None]:
        value = await self.client.get(key)
        if encoding is None or value is None:
            return value
        return value.decode(encoding)

    async def _gets(
        self,
        key: Union[bytes, str],
        encoding: str = "utf-8",
        _conn: Union[_Conn, None] = None,
    ) -> Union[int, None]:
        key = key.encode() if isinstance(key, str) else key
        _, token = await self.client.gets(key)
        return token

    @overload
    async def _multi_get(
        self,
        keys: Iterable[bytes],
        encoding: str = "utf-8",
        _conn: Union[_Conn, None] = None,
    ) -> List[Union[str, None]]: ...

    @overload
    async def _multi_get(
        self,
        keys: Iterable[bytes],
        encoding: None,
        _conn: Union[_Conn, None] = None,
    ) -> List[Union[bytes, None]]: ...

    async def _multi_get(
        self,
        keys: Iterable[bytes],
        encoding: Union[str, None] = "utf-8",
        _conn: Union[_Conn, None] = None,
    ) -> Union[
        List[Union[str, None]],
        List[Union[bytes, None]],
    ]:
        raw_values = await self.client.multi_get(*keys)
        if encoding is None:
            return list(raw_values)

        return [
            None if value is None else value.decode(encoding) for value in raw_values
        ]

    async def _set(
        self,
        key: bytes,
        value: Union[str, bytes],
        ttl: int = 0,
        _cas_token: Union[int, None] = None,
        _conn: Union[_Conn, None] = None,
    ) -> bool:
        value = value.encode() if isinstance(value, str) else value
        if _cas_token is not None:
            return await self._cas(key, value, _cas_token, ttl=ttl, _conn=_conn)
        try:
            return await self.client.set(key, value, exptime=ttl or 0)
        except aiomcache.exceptions.ValidationException as e:
            raise TypeError("aiomcache error: {}".format(str(e)))

    async def _cas(
        self,
        key: bytes,
        value: Union[str, bytes],
        token: int,
        ttl: Union[int, None] = None,
        _conn: Union[_Conn, None] = None,
    ) -> bool:
        value = str.encode(value) if isinstance(value, str) else value
        return await self.client.cas(key, value, token, exptime=ttl or 0)

    async def _multi_set(
        self,
        pairs: Iterable[Tuple[bytes, Union[str, bytes]]],
        ttl: int = 0,
        _conn: Union[_Conn, None] = None,
    ) -> bool:
        tasks = []
        for key, value in pairs:
            value = str.encode(value) if isinstance(value, str) else value
            tasks.append(self.client.set(key, value, exptime=ttl or 0))

        try:
            await asyncio.gather(*tasks)
        except aiomcache.exceptions.ValidationException as e:
            raise TypeError("aiomcache error: {}".format(str(e)))

        return True

    async def _add(
        self,
        key: bytes,
        value: Union[str, bytes],
        ttl: int = 0,
        _conn: Union[_Conn, None] = None,
    ) -> bool:
        value_bytes = str.encode(value) if isinstance(value, str) else value
        try:
            ret = await self.client.add(key, value_bytes, exptime=ttl or 0)
        except aiomcache.exceptions.ValidationException as e:
            raise TypeError("aiomcache error: {}".format(str(e)))
        if not ret:
            raise ValueError(
                "Key {!r} already exists, use .set to update the value".format(key)
            )

        return True

    async def _exists(self, key: bytes, _conn: Union[_Conn, None] = None) -> bool:
        return await self.client.append(key, b"")

    async def _increment(
        self, key: bytes, delta: int, _conn: Union[_Conn, None] = None
    ) -> int:
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
                raise TypeError("aiomcache error: {}".format(str(e)))

        return incremented or delta

    async def _expire(
        self, key: bytes, ttl: int, _conn: Union[_Conn, None] = None
    ) -> bool:
        return await self.client.touch(key, ttl)

    async def _delete(
        self, key: bytes, _conn: Union[str, None] = None
    ) -> Literal[1, 0]:
        return 1 if await self.client.delete(key) else 0

    async def _clear(
        self, namespace: Union[str, None] = None, _conn: Union[_Conn, None] = None
    ) -> bool:
        if namespace:
            raise ValueError("MemcachedCache doesnt support flushing by namespace")
        else:
            await self.client.flush_all()
        return True

    async def _raw(
        self,
        command: str,
        *args: Any,
        encoding: str = "utf-8",
        _conn: Union[_Conn, None] = None,
        **kwargs: Any,
    ) -> Any:
        value = await getattr(self.client, command)(*args, **kwargs)
        if command in {"get", "multi_get"}:
            if encoding is not None and value is not None:
                return value.decode(encoding)
        return value

    async def _redlock_release(self, key: bytes, _: Any) -> Literal[1, 0]:
        # Not ideal, should check the value coincides first but this would introduce
        # race conditions
        return await self._delete(key)

    async def _close(
        self, *args: Any, _conn: Union[_Conn, None] = None, **kwargs: Any
    ) -> None:
        await self.client.close()

    def build_key(self, key: str, namespace: Union[str, None] = None) -> bytes:
        ns_key = self._str_build_key(key, namespace).replace(" ", "_")
        return str.encode(ns_key)

    @classmethod
    def parse_uri_path(cls, path: str) -> Dict[Any, Any]:
        return {}

    def __repr__(self) -> str:  # pragma: no cover
        return "MemcachedCache ({}:{})".format(self.host, self.port)
