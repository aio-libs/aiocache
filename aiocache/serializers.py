from typing import Any

from aiocache.log import logger


try:
    import ujson as json
except ImportError:
    logger.warning("ujson module not found, usin json")
    import json

import pickle


class NullSerializer:
    """
    This serializer does nothing. Its only recommended to be used by
    :class:`aiocache.SimpleMemoryCache` because for other backends it will
    produce incompatible data unless you work only with str types.

    DISCLAIMER: Be careful with mutable types and memory storage. The following
    behavior is considered normal (same as ``functools.lru_cache``)::

        cache = SimpleMemoryCache()
        my_list = [1]
        await cache.set("key", my_list)
        my_list.append(2)
        await cache.get("key")  # Will return [1, 2]
    """
    encoding = 'utf-8'

    @classmethod
    def dumps(cls, value: Any) -> Any:
        """
        Returns the same value
        """
        return value

    @classmethod
    def loads(cls, value: Any) -> Any:
        """
        Returns the same value
        """
        return value


class StringSerializer:
    """
    Converts all input values to str. All return values are also str. Be
    careful because this means that if you store an ``int(1)``, you will get
    back '1'.

    The transformation is done by just casting to str in the ``dumps`` method.

    If you want to keep python types, use ``PickleSerializer``. ``JsonSerializer``
    may also be useful to keep type of symple python types.
    """
    encoding = 'utf-8'

    @classmethod
    def dumps(cls, value: Any) -> str:
        """
        Serialize the received value casting it to str.
        """
        return str(value)

    @classmethod
    def loads(cls, value: Any) -> str:
        """
        Returns value back without transformations
        """
        return value


class PickleSerializer:
    """
    Transform data to bytes using pickle.dumps and pickle.loads to retrieve it back.
    """
    encoding = None

    @classmethod
    def dumps(cls, value: Any) -> bytes:
        """
        Serialize the received value using ``pickle.dumps``.
        """
        return pickle.dumps(value)

    @classmethod
    def loads(cls, value: bytes) -> Any:
        """
        Deserialize value using ``pickle.loads``.
        """
        if value is None:
            return None
        return pickle.loads(value)


class JsonSerializer:
    """
    Transform data to json string with json.dumps and json.loads to retrieve it back. Check
    https://docs.python.org/3/library/json.html#py-to-json-table for how types are converted.
    """
    encoding = 'utf-8'

    @classmethod
    def dumps(cls, value: dict) -> str:
        """
        Serialize the received value using ``json.dumps``.
        """
        return json.dumps(value)

    @classmethod
    def loads(cls, value: str) -> Any:
        """
        Deserialize value using ``json.loads``.
        """
        if value is None:
            return None
        return json.loads(value)
