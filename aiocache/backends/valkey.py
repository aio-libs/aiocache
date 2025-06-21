import logging
import sys
from typing import Any, Iterable, Literal, Mapping, Optional, TypedDict, Union, overload

from glide import (
    ConditionalChange,
    ExpirySet,
    ExpiryType,
    GlideClient,
    GlideClientConfiguration,
    Transaction,
)
from glide.exceptions import RequestError as IncrbyException

from aiocache.base import BaseCache, BaseCacheArgs, _Conn
from aiocache.serializers import JsonSerializer

if sys.version_info >= (3, 11):
    from typing import Self, Unpack
else:
    from typing_extensions import Self, Unpack  # noqa: I900


logger = logging.getLogger(__name__)


class _AddKwargs(TypedDict, total=False):
    conditional_set: ConditionalChange
    expiry: Optional[ExpirySet]
    return_old_value: bool


class ValkeyCache(BaseCache[str]):
    """
    Valkey cache implementation with the following components as defaults:
        - serializer: :class:`aiocache.serializers.JsonSerializer`
        - plugins: []

    Config options are:

    :param serializer: obj derived from :class:`aiocache.serializers.BaseSerializer`.
    :param plugins: list of :class:`aiocache.plugins.BasePlugin` derived classes.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend. Default is an empty string, "".
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.
    :param client: glide.GlideClient which is an active client for working with valkey
    """

    NAME = "valkey"

    def __init__(
        self, config: GlideClientConfiguration, **kwargs: Unpack[BaseCacheArgs]
    ) -> None:
        self.config = config

        if "serializer" not in kwargs:
            kwargs["serializer"] = JsonSerializer()
        if "key_builder" not in kwargs:
            kwargs["key_builder"] = lambda k, ns: f"{ns}:{k}" if ns else k

        super().__init__(**kwargs)

    async def __aenter__(self) -> Self:
        self.client = await GlideClient.create(self.config)
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.client.close()

    @overload
    async def _get(
        self,
        key: str,
        encoding: str = "utf-8",
        _conn: Union[_Conn, None] = None,
    ) -> Union[str, None]: ...

    @overload
    async def _get(
        self, key: str, encoding: None, _conn: Union[_Conn, None] = None
    ) -> Union[bytes, None]: ...

    async def _get(
        self,
        key: str,
        encoding: Union[str, None] = "utf-8",
        _conn: Union[_Conn, None] = None,
    ) -> Union[str, bytes, None]:
        value = await self.client.get(key)
        if encoding is None or value is None:
            return value
        return value.decode(encoding)

    _gets = _get

    @overload
    async def _multi_get(
        self,
        keys: list[str],
        encoding: str = "utf-8",
        _conn: Union[_Conn, None] = None,
    ) -> list[Union[str, None]]: ...

    @overload
    async def _multi_get(
        self,
        keys: list[str],
        encoding: None,
        _conn: Union[_Conn, None] = None,
    ) -> list[Union[bytes, None]]: ...

    async def _multi_get(
        self,
        keys: list[str],
        encoding: Union[str, None] = "utf-8",
        _conn: Union[_Conn, None] = None,
    ) -> Union[
        list[Union[str, None]],
        list[Union[bytes, None]],
    ]:
        values = await self.client.mget(keys)  # type: ignore[arg-type]
        if encoding is None:
            return values
        return [v if v is None else v.decode(encoding) for v in values]

    async def _set(
        self,
        key: str,
        value: Union[str, bytes],
        ttl: Union[float, int, None] = None,
        _cas_token: Union[str, None] = None,
        _conn: Union[_Conn, None] = None,
    ) -> bool:
        if isinstance(ttl, float):
            ttl_ = ExpirySet(ExpiryType.MILLSEC, int(ttl * 1000))
        elif ttl:
            ttl_ = ExpirySet(ExpiryType.SEC, ttl)
        else:
            ttl_ = None

        if _cas_token is not None:
            return await self._cas(key, value, _cas_token, ttl=ttl_, _conn=_conn)

        return await self.client.set(key, value, expiry=ttl_) == "OK"  # type: ignore[comparison-overlap]

    async def _cas(
        self,
        key: str,
        value: Union[str, bytes],
        token: str,
        ttl: Union[ExpirySet, int, None] = None,
        _conn: Union[_Conn, None] = None,
    ) -> bool:
        if await self._get(key) == token:
            if isinstance(ttl, int):
                ttl = ExpirySet(ExpiryType.SEC, ttl)
            return await self.client.set(key, value, expiry=ttl) == "OK"  # type: ignore[comparison-overlap]
        return False

    async def _multi_set(
        self,
        pairs: Iterable[tuple[str, Union[str, bytes]]],
        ttl: Union[int, None] = None,
        _conn: Union[_Conn, None] = None,
    ) -> bool:
        values = dict(pairs)

        if ttl:
            await self.__multi_set_ttl(values, ttl)
        else:
            await self.client.mset(values)  # type: ignore[arg-type]

        return True

    async def __multi_set_ttl(
        self, values: Mapping[str, Union[str, bytes]], ttl: int
    ) -> None:
        transaction = Transaction()
        transaction.mset(values)  # type: ignore[arg-type]
        ttl, exp = (
            (int(ttl * 1000), transaction.pexpire)
            if isinstance(ttl, float)
            else (ttl, transaction.expire)
        )
        for key in values:
            exp(key, ttl)
        await self.client.exec(transaction)

    async def _add(
        self,
        key: str,
        value: Union[str, bytes],
        ttl: Union[float, int, None] = None,
        _conn: Union[_Conn, None] = None,
    ) -> Literal["OK"]:
        kwargs: _AddKwargs = {
            "conditional_set": ConditionalChange.ONLY_IF_DOES_NOT_EXIST
        }
        if isinstance(ttl, float):
            kwargs["expiry"] = ExpirySet(ExpiryType.MILLSEC, int(ttl * 1000))
        elif ttl:
            kwargs["expiry"] = ExpirySet(ExpiryType.SEC, ttl)

        was_set = await self.client.set(key, value, **kwargs)
        if was_set != "OK":  # type: ignore[comparison-overlap]
            raise ValueError(
                "Key {} already exists, use .set to update the value".format(key)
            )
        return was_set  # type: ignore[return-value]

    async def _exists(self, key: str, _conn: Union[_Conn, None] = None) -> bool:
        return bool(await self.client.exists([key]))

    async def _increment(
        self, key: str, delta: int, _conn: Union[_Conn, None] = None
    ) -> int:
        try:
            return await self.client.incrby(key, delta)
        except IncrbyException:
            raise TypeError("Value is not an integer") from None

    async def _expire(
        self, key: str, ttl: int, _conn: Union[_Conn, None] = None
    ) -> bool:
        if ttl == 0:
            return await self.client.persist(key)
        return await self.client.expire(key, ttl)

    async def _delete(self, key: str, _conn: Union[_Conn, None] = None) -> int:
        return await self.client.delete([key])

    async def _clear(
        self, namespace: Union[str, None] = None, _conn: Union[_Conn, None] = None
    ) -> Union[Literal["OK"], bool]:
        if not namespace:
            return await self.client.flushdb()

        _, keys = await self.client.scan(b"0", "{}:*".format(namespace))
        if keys:
            return bool(await self.client.delete(keys))  # type: ignore[arg-type]

        return True

    async def _raw(
        self,
        command: str,
        *args: Any,
        encoding: Union[str, None] = "utf-8",
        _conn: Union[_Conn, None] = None,
        **kwargs: Any,
    ) -> Any:
        value = await getattr(self.client, command)(*args, **kwargs)
        if encoding is not None:
            if command == "get" and value is not None:
                value = value.decode(encoding)
        return value

    async def _redlock_release(self, key: str, value: Union[str, bytes]) -> int:
        if await self._get(key) == value:
            return await self.client.delete([key])
        return 0

    def build_key(self, key: str, namespace: Optional[str] = None) -> str:
        return self._str_build_key(key, namespace)

    @classmethod
    def parse_uri_path(cls, path: str) -> dict[str, str]:
        """
        Given a uri path, return the Valkey specific configuration
        options in that path string according to iana definition
        http://www.iana.org/assignments/uri-schemes/prov/redis

        :param path: string containing the path. Example: "/0"
        :return: mapping containing the options. Example: {"db": "0"}
        """
        options = {}
        db, *_ = path[1:].split("/")
        if db:
            options["db"] = db
        return options

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ValkeyCache ({self.client.config.addresses[0].host}"
            f":{self.client.config.addresses[0].port})"
        )
