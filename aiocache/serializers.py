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

    encoding = "utf-8"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abc.abstractmethod
    def serialize(self, value):
        pass

    @abc.abstractmethod
    def deserialize(self, value):
        pass


class DefaultSerializer(BaseSerializer):
    """
    Dummy serializer that returns the same value passed both in serialize and
    deserialize methods.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def serialize(self, value):
        return value

    def deserialize(self, value):
        return value


class PickleSerializer(BaseSerializer):

    encoding = None

    def serialize(self, value):
        return pickle.dumps(value)

    def deserialize(self, value):
        return pickle.loads(value)


class JsonSerializer(BaseSerializer):

    def serialize(self, value):
        # Serialize with bytes
        return json.dumps(value)

    def deserialize(self, value):
        return json.loads(value)
