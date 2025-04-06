import logging
import time
from typing import Any, Callable, Optional, TYPE_CHECKING, List, cast

from glide import GlideClient, Script, Transaction, ExpirySet, ExpiryType, ConditionalChange
from glide.exceptions import RequestError as IncrbyException
from glide.protobuf.command_request_pb2 import RequestType

from aiocache.base import BaseCache, API
from aiocache.serializers import JsonSerializer

if TYPE_CHECKING:  # pragma: no cover
    from aiocache.serializers import BaseSerializer


logger = logging.getLogger(__name__)


class ValkeyBackend(BaseCache[str]):
    def __init__(
        self,
        client: GlideClient,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.client = client

    async def _get(self, key, encoding="utf-8", _conn=None):
        value = await self.client.get(key)
        if encoding is None or value is None:
            return value
        return value.decode(encoding)

    async def _gets(self, key, encoding="utf-8", _conn=None):
        return await self._get(key, encoding=encoding, _conn=_conn)

    async def _multi_get(self, keys, encoding="utf-8", _conn=None):
        values = await self.client.mget(keys)
        if encoding is None:
            return values
        return [v if v is None else v.decode(encoding) for v in values]

    async def _set(self, key, value, ttl=None, _cas_token=None, _conn=None):
        success_message = "OK"

        if isinstance(ttl, float):
            ttl = ExpirySet(ExpiryType.MILLSEC, int(ttl * 1000))
        elif ttl:
            ttl = ExpirySet(ExpiryType.SEC, ttl)

        if _cas_token is not None:
            return await self._cas(key, value, _cas_token, ttl=ttl, _conn=_conn)

        if ttl is None:
            return await self.client.set(key, value) == success_message

        return await self.client.set(key, value, expiry=ttl) == success_message

    async def _cas(self, key, value, token, ttl=None, _conn=None):
        if await self._get(key) == token:
            return await self.client.set(key, value, expiry=ttl) == "OK"
        return 0

    async def _multi_set(self, pairs, ttl=None, _conn=None):
        ttl = ttl or 0

        values = {key: value for key, value in pairs}

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
            raise ValueError("Key {} already exists, use .set to update the value".format(key))
        return was_set

    async def _exists(self, key, _conn=None):
        if isinstance(key, str):
            key = [key]
        number = await self.client.exists(key)
        return bool(number)

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
        if isinstance(key, str):
            key = [key]
        return await self.client.delete(key)

    async def _clear(self, namespace=None, _conn=None):
        if namespace:
            _, keys = await self.client.scan(b"0", "{}:*".format(namespace))
            if keys:
                return bool(await self.client.delete(keys))
        else:
            return await self.client.flushdb()

        return True

    @API.register
    @API.aiocache_enabled()
    @API.timeout
    @API.plugins
    async def script(self, script: Script, keys: List, *args):
        """
        Send the raw scripts to the underlying client. Note that by using this CMD you
        will lose compatibility with other backends.

        Due to limitations with aiomcache client, args have to be provided as bytes.
        For rest of backends, str.

        :param script: glide.Script object.
        :param keys: list of keys of the script
        :param args: arguments of the script
        :returns: whatever the underlying client returns
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self.timeout
        """
        start = time.monotonic()
        ret = await self._script(script, keys, *args)
        logger.debug("%s (%.4f)s", script, time.monotonic() - start)
        return ret

    async def _script(self, script, keys: List, *args):
        return await self.client.invoke_script(script, keys=keys, args=args)

    async def _raw(self, command, *args, encoding="utf-8", _conn=None, **kwargs):
        value = await getattr(self.client, command)(*args, **kwargs)
        if encoding is not None:
            if command == "get" and value is not None:
                value = value.decode(encoding)
            elif command in {"keys", "mget"}:
                value = [v if v is None else v.decode(encoding) for v in value]
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
        client: GlideClient,
        serializer: Optional["BaseSerializer"] = None,
        namespace: str = "",
        key_builder: Callable[[str, str], str] = lambda k, ns: f"{ns}:{k}" if ns else k,
        **kwargs: Any,
    ):
        super().__init__(
            client=client,
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
        return "ValkeyCache"
