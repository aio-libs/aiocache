from aiocache.log import logger


try:
    import ujson as json
except ImportError:
    logger.warning("ujson module not found, usin json")
    import json

try:
    import cPickle as pickle
except ImportError:
    logger.warning("cPickle module not found, using pickle")
    import pickle


class DefaultSerializer:
    """
    Dummy serializer that returns the same value passed both in serialize and
    deserialize methods.

    There is an edge case to take into account with python types. Due to backends
    working with bytes, although it may be possible to save an ``int`` type, when
    retrieving it it will become an str. If you want to keep types, you will have
    to use something like ``PickleSerializer`` or marshmallow custom serializer
    class.
    """
    encoding = 'utf-8'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dumps(self, value):
        return value

    def loads(self, value):
        return value


class PickleSerializer(DefaultSerializer):
    """
    Transform data to bytes using pickle.dumps and pickle.loads to retrieve it back.
    """
    encoding = None

    def dumps(self, value):
        """
        Serialize the received value using ``pickle.dumps``.

        :param value: obj
        :returns: bytes
        """
        return pickle.dumps(value)

    def loads(self, value):
        """
        Deserialize value using ``pickle.loads``.

        :param value: bytes
        :returns: obj
        """
        if value is None:
            return None
        return pickle.loads(value)


class JsonSerializer(DefaultSerializer):
    """
    Transform data to json string with json.dumps and json.loads to retrieve it back.
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
        :returns: dict
        """
        if value is None:
            return None
        return json.loads(value)
