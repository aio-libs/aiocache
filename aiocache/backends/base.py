import abc

from aiocache.serializers import DefaultSerializer


class BaseCache(metaclass=abc.ABCMeta):
    """
    Base class that agregates the common logic for the different caches that may exist
    """

    def get_serializer(self):
        return DefaultSerializer()

    async def add(self, key, value):
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, key, default=None):
        pass

    @abc.abstractmethod
    async def multi_get(self, keys):
        pass

    @abc.abstractmethod
    async def set(self, key, value, ttl=None):
        pass

    @abc.abstractmethod
    async def multi_set(self, pairs):
        pass

    @abc.abstractmethod
    async def delete(self, key):
        pass

    async def expire(self, key, ttl):
        raise NotImplementedError

    async def ttl(self, key):
        raise NotImplementedError

    async def persist(self, key):
        raise NotImplementedError

    def _build_key(self, key):
        if self.namespace:
            return "{}:{}".format(self.namespace, key)
        return key
