import logging
import sys
from typing import Any, Callable, Optional

from glide import (
    ConditionalChange,
    ExpirySet,
    ExpiryType,
    GlideClient,
    GlideClientConfiguration,
    Transaction,
)
from glide.exceptions import RequestError as IncrbyException

from aiocache.base import BaseCache
from aiocache.serializers import BaseSerializer, JsonSerializer

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing import Any as Self


logger = logging.getLogger(__name__)


class ValkeyBackend(BaseCache[str]):
    def __init__(self, config: GlideClientConfiguration, **kwargs):
        self.config = config
        super().__init__(**kwargs)

    async def __aenter__(self) -> Self:
        self.client = await GlideClient.create(self.config)
        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.client.close()

    async def _get(self, key, encoding="utf-8", _conn=None):
        value = await self.client.get(key)
        if encoding is None or value is None:
            return value
        return value.decode(encoding)

    _gets = _get

    async def _multi_get(self, keys, encoding="utf-8", _conn=None):
        values = await self.client.mget(keys)
        if encoding is None:
            return values
        return [v if v is None else v.decode(encoding) for v in values]

    async def _set(self, key, value, ttl=None, _cas_token=None, _conn=None):
        if isinstance(ttl, float):
            ttl = ExpirySet(ExpiryType.MILLSEC, int(ttl * 1000))
        elif ttl:
            ttl = ExpirySet(ExpiryType.SEC, ttl)

        if _cas_token is not None:
            return await self._cas(key, value, _cas_token, ttl=ttl, _conn=_conn)

        return await self.client.set(key, value, expiry=ttl) == "OK"

    async def _cas(self, key, value, token, ttl=None, _conn=None):
        if await self._get(key) == token:
            return await self.client.set(key, value, expiry=ttl) == "OK"
        return 0

    async def _multi_set(self, pairs, ttl=None, _conn=None):
        values = dict(pairs)

        if ttl:
            await self.__multi_set_ttl(values, ttl)
        else:
            await self.client.mset(values)

        return True

    async def __multi_set_ttl(self, values, ttl):
        transaction = Transaction()
        transaction.mset(values)
        ttl, exp = (
            (int(ttl * 1000), transaction.pexpire)
            if isinstance(ttl, float)
            else (ttl, transaction.expire)
        )
        for key in values:
            exp(key, ttl)
        await self.client.exec(transaction)

    async def _add(self, key, value, ttl=None, _conn=None):
        kwargs = {"conditional_set": ConditionalChange.ONLY_IF_DOES_NOT_EXIST}
        if isinstance(ttl, float):
            kwargs["expiry"] = ExpirySet(ExpiryType.MILLSEC, int(ttl * 1000))
        elif ttl:
            kwargs["expiry"] = ExpirySet(ExpiryType.SEC, ttl)
        was_set = await self.client.set(key, value, **kwargs)
        if was_set != "OK":
            raise ValueError(
                "Key {} already exists, use .set to update the value".format(key)
            )
        return was_set

    async def _exists(self, key, _conn=None):
        return bool(await self.client.exists([key]))

    async def _increment(self, key, delta, _conn=None):
        try:
            return await self.client.incrby(key, delta)
        except IncrbyException:
            raise TypeError("Value is not an integer") from None

    async def _expire(self, key, ttl, _conn=None):
        if ttl == 0:
            return await self.client.persist(key)
        return await self.client.expire(key, ttl)

    async def _delete(self, key, _conn=None):
        return await self.client.delete([key])

    async def _clear(self, namespace=None, _conn=None):
        if not namespace:
            return await self.client.flushdb()

        _, keys = await self.client.scan(b"0", "{}:*".format(namespace))
        if keys:
            return bool(await self.client.delete(keys))

        return True

    async def _raw(self, command, *args, encoding="utf-8", _conn=None, **kwargs):
        value = await getattr(self.client, command)(*args, **kwargs)
        if encoding is not None:
            if command == "get" and value is not None:
                value = value.decode(encoding)
        return value

    async def _redlock_release(self, key, value):
        if await self._get(key) == value:
            return await self.client.delete([key])
        return 0

    def build_key(self, key: str, namespace: Optional[str] = None) -> str:
        return self._str_build_key(key, namespace)


class ValkeyCache(ValkeyBackend):
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
        self,
        config: GlideClientConfiguration,
        serializer: Optional[BaseSerializer] = None,
        namespace: str = "",
        key_builder: Callable[[str, str], str] = lambda k, ns: f"{ns}:{k}" if ns else k,
        **kwargs: Any,
    ):
        super().__init__(
            config,
            serializer=serializer or JsonSerializer(),
            namespace=namespace,
            key_builder=key_builder,
            **kwargs,
        )

    @classmethod
    def parse_uri_path(cls, path):
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

    def __repr__(self):  # pragma: no cover
        return (
            f"ValkeyCache ({self.client.config.addresses[0].host}"
            f":{self.client.config.addresses[0].port})"
        )
