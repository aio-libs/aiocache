import logging
import pickle  # noqa: S403
from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

logger = logging.getLogger(__name__)
_T = TypeVar("_T")

try:
    import ujson as json  # noqa: I900
except ImportError:
    logger.debug("ujson module not found, using json")
    import json  # type: ignore[no-redef]

try:
    import msgpack
except ImportError:
    msgpack = None
    logger.debug("msgpack not installed, MsgPackSerializer unavailable")

try:
    from msgspec.msgpack import Decoder as MsgspecDecoder
    from msgspec.msgpack import Encoder as MsgspecEncoder
except ImportError:
    MsgspecEncoder = None

    # Only here as extended typehinting
    class MsgspecDecoder(Generic[_T]):
        def decode(self, buf: Union[bytes, bytearray, memoryview[int]]) -> _T: ...

    logger.debug("msgspec not installed, MsgspecSerlizer unavailable")

_NOT_SET = object()


class BaseSerializer(ABC):
    DEFAULT_ENCODING: Optional[str] = "utf-8"

    def __init__(self, *args, encoding=_NOT_SET, **kwargs):
        self.encoding = self.DEFAULT_ENCODING if encoding is _NOT_SET else encoding
        super().__init__(*args, **kwargs)

    @abstractmethod
    def dumps(self, value: Any, /) -> Any:
        """Serialise the value to be stored in the backend."""

    @abstractmethod
    def loads(self, value: Any, /) -> Any:
        """Decode the value retrieved from the backend."""


class NullSerializer(BaseSerializer):
    """
    This serializer does nothing. Its only recommended to be used by
    :class:`aiocache.SimpleMemoryCache` because for other backends it will
    produce incompatible data unless you work only with str types because it
    store data as is.

    DISCLAIMER: Be careful with mutable types and memory storage. The following
    behavior is considered normal (same as ``functools.lru_cache``)::

        cache = Cache()
        my_list = [1]
        await cache.set("key", my_list)
        my_list.append(2)
        await cache.get("key")  # Will return [1, 2]
    """

    def dumps(self, value):
        """
        Returns the same value
        """
        return value

    def loads(self, value):
        """
        Returns the same value
        """
        return value


class StringSerializer(BaseSerializer):
    """
    Converts all input values to str. All return values are also str. Be
    careful because this means that if you store an ``int(1)``, you will get
    back '1'.

    The transformation is done by just casting to str in the ``dumps`` method.

    If you want to keep python types, use ``PickleSerializer``. ``JsonSerializer``
    may also be useful to keep type of simple python types.
    """

    def dumps(self, value):
        """
        Serialize the received value casting it to str.

        :param value: obj Anything support cast to str
        :returns: str
        """
        return str(value)

    def loads(self, value):
        """
        Returns value back without transformations
        """
        return value


class PickleSerializer(BaseSerializer):
    """
    Transform data to bytes using pickle.dumps and pickle.loads to retrieve it back.
    """

    DEFAULT_ENCODING = None

    def __init__(self, *args, protocol=pickle.DEFAULT_PROTOCOL, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol = protocol

    def dumps(self, value):
        """
        Serialize the received value using ``pickle.dumps``.

        :param value: obj
        :returns: bytes
        """
        return pickle.dumps(value, protocol=self.protocol)

    def loads(self, value):
        """
        Deserialize value using ``pickle.loads``.

        :param value: bytes
        :returns: obj
        """
        if value is None:
            return None
        return pickle.loads(value)  # noqa: S301


class JsonSerializer(BaseSerializer):
    """
    Transform data to json string with json.dumps and json.loads to retrieve it back. Check
    https://docs.python.org/3/library/json.html#py-to-json-table for how types are converted.

    ujson will be used by default if available. Be careful with differences between built in
    json module and ujson:
        - ujson dumps supports bytes while json doesn't
        - ujson and json outputs may differ sometimes
    """

    def dumps(self, value):
        """
        Serialize the received value using ``json.dumps``.

        :param value: dict
        :returns: str
        """
        return json.dumps(value)

    def loads(self, value):
        """
        Deserialize value using ``json.loads``.

        :param value: str
        :returns: output of ``json.loads``.
        """
        if value is None:
            return None
        return json.loads(value)


class MsgPackSerializer(BaseSerializer):
    """
    Transform data to bytes using msgpack.dumps and msgpack.loads to retrieve it back. You need
    to have ``msgpack`` installed in order to be able to use this serializer.

    :param encoding: str. Can be used to change encoding param for ``msg.loads`` method.
        Default is utf-8.
    :param use_list: bool. Can be used to change use_list param for ``msgpack.loads`` method.
        Default is True.
    """

    def __init__(self, *args, use_list=True, **kwargs):
        if not msgpack:
            raise RuntimeError("msgpack not installed, MsgPackSerializer unavailable")
        self.use_list = use_list
        super().__init__(*args, **kwargs)

    def dumps(self, value):
        """
        Serialize the received value using ``msgpack.dumps``.

        :param value: obj
        :returns: bytes
        """
        return msgpack.dumps(value)

    def loads(self, value):
        """
        Deserialize value using ``msgpack.loads``.

        :param value: bytes
        :returns: obj
        """
        raw = False if self.encoding == "utf-8" else True
        if value is None:
            return None
        return msgpack.loads(value, raw=raw, use_list=self.use_list)


class MsgspecSerializer(BaseSerializer, Generic[_T]):
    @overload
    def __init__(
        self: "MsgspecSerializer[Any]",
        enc_hook: Optional[Callable[[Any], Any]] = None,
        decimal_format: Literal["string", "number"] = "string",
        uuid_format: Literal["canonical", "hex", "bytes"] = "canonical",
        order: Literal["deterministic", "sorted"] | None = None,
        struct_type: None = None,
        strict: bool = True,
        dec_hook: Optional[Callable[[Type, Any], Any]] = None,
        ext_hook: Optional[Callable[[int, memoryview[int]], Any]] = None,
    ) -> None: ...

    @overload
    def __init__(
        self: "MsgspecSerializer[_T]",
        enc_hook: Optional[Callable[[Any], Any]] = None,
        decimal_format: Literal["string", "number"] = "string",
        uuid_format: Literal["canonical", "hex", "bytes"] = "canonical",
        order: Literal["deterministic", "sorted"] | None = None,
        struct_type: Type[_T] = None,
        strict: bool = True,
        dec_hook: Optional[Callable[[type, Any], Any]] = None,
        ext_hook: Optional[Callable[[int, memoryview[int]], Any]] = None,
    ) -> None: ...

    def __init__(
        self,
        enc_hook: Optional[Callable[[Any], Any]] = None,
        decimal_format: Literal["string", "number"] = "string",
        uuid_format: Literal["canonical", "hex", "bytes"] = "canonical",
        order: Literal["deterministic", "sorted"] | None = None,
        struct_type: Type[_T] | None = None,
        strict: bool = True,
        dec_hook: Optional[Callable[[type, Any], Any]] = None,
        ext_hook: Optional[Callable[[int, memoryview[int]], Any]] = None,
    ):
        if MsgspecEncoder is None:
            raise RuntimeError("msgspec not installed, MsgspecSerializer unavailable")

        self.encoder = MsgspecEncoder(
            enc_hook=enc_hook,
            decimal_format=decimal_format,
            uuid_format=uuid_format,
            order=order,
        )

        if struct_type is not None:
            self.decoder: "MsgspecDecoder[_T]" = MsgspecDecoder(
                type=struct_type, dec_hook=dec_hook, ext_hook=ext_hook, strict=strict
            )
        else:
            self.decoder: "MsgspecDecoder[Any]" = MsgspecDecoder(
                dec_hook=dec_hook, ext_hook=ext_hook, strict=strict
            )

    @overload
    def dumps(self, value: _T) -> bytes: ...

    @overload
    def dumps(self, value: Any) -> bytes: ...

    def dumps(self, value: _T | Any) -> bytes:
        return self.encoder.encode(value)

    def loads(self, value: bytes) -> _T:
        return self.decoder.decode(value)
