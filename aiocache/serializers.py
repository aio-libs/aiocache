import abc
import logging


logger = logging.getLogger(__name__)

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


class BaseSerializer(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def dumps(self, value):
        pass

    @abc.abstractmethod
    def loads(self, value):
        pass


class DefaultSerializer(BaseSerializer):
    """
    Dummy serializer that returns the same value passed both in serialize and
    deserialize methods.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dumps(self, value):
        return value

    def loads(self, value):
        return value


class PickleSerializer(BaseSerializer):
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


class JsonSerializer(BaseSerializer):
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
        return json.loads(value)
