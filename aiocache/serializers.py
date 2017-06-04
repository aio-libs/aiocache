from aiocache.log import logger


try:
    import ujson as json
except ImportError:
    logger.warning("ujson module not found, usin json")
    import json

import pickle


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def dumps(cls, value):
        """
        Serialize the received value casting it to str.

        :param value: obj Anything support cast to str
        :returns: str
        """
        return str(value)

    @classmethod
    def loads(cls, value):
        """
        Returns value back without transformations
        """
        return value


class PickleSerializer(StringSerializer):
    """
    Transform data to bytes using pickle.dumps and pickle.loads to retrieve it back.
    """
    encoding = None

    @classmethod
    def dumps(cls, value):
        """
        Serialize the received value using ``pickle.dumps``.

        :param value: obj
        :returns: bytes
        """
        return pickle.dumps(value)

    @classmethod
    def loads(cls, value):
        """
        Deserialize value using ``pickle.loads``.

        :param value: bytes
        :returns: obj
        """
        if value is None:
            return None
        return pickle.loads(value)


class JsonSerializer(StringSerializer):
    """
    Transform data to json string with json.dumps and json.loads to retrieve it back. Check
    https://docs.python.org/3/library/json.html#py-to-json-table for how types are converted.
    """

    @classmethod
    def dumps(cls, value):
        """
        Serialize the received value using ``json.dumps``.

        :param value: dict
        :returns: str
        """
        return json.dumps(value)

    @classmethod
    def loads(cls, value):
        """
        Deserialize value using ``json.loads``.

        :param value: str
        :returns: output of ``json.loads``.
        """
        if value is None:
            return None
        return json.loads(value)
