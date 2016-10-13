import abc

from aiocache.serializers import DefaultSerializer
from aiocache.policies import DefaultPolicy


class BaseCache(metaclass=abc.ABCMeta):
    """
    Base class that agregates the common logic for the different caches that may exist. Available
    options are:

    :param serializer: obj with :class:`aiocache.serializers.BaseSerializer` interface.
        Must implement ``loads`` and ``dumps`` methods.
    :param policy: obj with :class:`aiocache.policies.DefaultPolicy` interface.
    :param namespace: string to use as prefix for the key used in all operations of the backend.
    :param max_keys: int indicating the max number of keys to store in the backend. If not
        specified or 0, it's unlimited.
    """

    def __init__(self, serializer=None, policy=None, namespace=None, max_keys=None):

        self.serializer = serializer or self.get_serializer()
        self.policy = policy or self.get_policy()
        self.namespace = namespace or ""
        self.max_keys = max_keys or None

    def get_serializer(self):
        return DefaultSerializer()

    def get_policy(self):
        return DefaultPolicy(self)

    @abc.abstractmethod
    async def add(self, key, value, ttl=None):  # pragma: no cover
        pass

    @abc.abstractmethod
    async def get(self, key, default=None):  # pragma: no cover
        pass

    @abc.abstractmethod
    async def multi_get(self, keys):  # pragma: no cover
        pass

    @abc.abstractmethod
    async def set(self, key, value, ttl=None):  # pragma: no cover
        pass

    @abc.abstractmethod
    async def multi_set(self, pairs):  # pragma: no cover
        pass

    @abc.abstractmethod
    async def delete(self, key):  # pragma: no cover
        pass

    @abc.abstractmethod
    async def exists(self, key):  # pragma: no cover
        pass

    async def expire(self, key, ttl):  # pragma: no cover
        raise NotImplementedError

    async def ttl(self, key):  # pragma: no cover
        raise NotImplementedError

    async def persist(self, key):  # pragma: no cover
        raise NotImplementedError

    def _build_key(self, key):
        if self.namespace:
            return "{}{}".format(self.namespace, key)
        return key
