import abc

from aiocache.serializers import DefaultSerializer


class BaseCache(metaclass=abc.ABCMeta):
    """
    Base class that agregates the common logic for the different caches that may exist
    """

    def get_serializer(self):
        return DefaultSerializer()

    async def add(self, key, value):
        """
        Add a value to the cache, if the key exists it fails.

        :param key: str
        :param value: obj
        :raises: ValueError
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, key, default=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param default: obj
        :returns: obj
        """
        pass

    @abc.abstractmethod
    async def multi_get(self, keys):
        """
        Return multiple objects identified by keys. If a key is not found
        it replaces it with a None

        :param keys: list of str
        """
        pass

    @abc.abstractmethod
    async def set(self, key, value, ttl=None):
        """
        Stores the value in the given key with ttl if specified

        :param key: str
        :param value: obj
        :param ttl: int the expiration time in seconds
        :returns:
        """
        pass

    @abc.abstractmethod
    async def multi_set(self, pairs):
        """
        Store multiple values in the specified keys

        :param pairs: list of two element iterables. First is key and second is value
        """
        pass

    @abc.abstractmethod
    async def delete(self, key):
        """
        Remove key from the cache

        :param key: str
        """
        pass

    async def expire(self, key, ttl):
        """
        Sets ttl to the given key

        :param key: str
        :param ttl: int the expiration time in seconds
        """
        raise NotImplementedError

    async def ttl(self, key):
        """
        Returns the time to live of a key in seconds.

        :param key: str
        :returns: time to live in seconds
        """
        raise NotImplementedError

    async def persist(self, key):
        """
        Remove the ttl for a key.

        :param key: str
        """
        raise NotImplementedError

    def _build_key(self, key):
        if self.namespace:
            return "{}:{}".format(self.namespace, key)
        return key
