import abc

from aiocache.serializers import DefaultSerializer


class BaseCache(metaclass=abc.ABCMeta):
    """
    Base class that agregates the common logic for the different caches that may exist
    """

    def get_serializer(self):
        return DefaultSerializer()

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
            return "{}:{}".format(self.namespace, key)
        return key
