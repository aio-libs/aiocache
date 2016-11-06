import time

import aiocache

from aiocache.log import logger
from aiocache.backends import SimpleMemoryBackend, RedisBackend, MemcachedBackend


class BaseCache:
    """
    Base class that agregates the common logic for the different caches that may exist. Available
    options are:

    :param serializer: obj with :class:`aiocache.serializers.BaseSerializer` interface.
        Must implement ``loads`` and ``dumps`` methods.
    :param namespace: string to use as prefix for the key used in all operations of the backend.
    :param max_keys: int indicating the max number of keys to store in the backend. If not
        specified or 0, it's unlimited.
    """

    def __init__(self, serializer=None, namespace=None, *args, **kwargs):

        self._backend = self.get_backend(*args, **{**aiocache.DEFAULT_KWARGS, **kwargs})
        self._serializer = None
        self.serializer = serializer or self.get_default_serializer()
        self._policy = self.get_default_policy()
        self.namespace = namespace or aiocache.DEFAULT_NAMESPACE

    def get_backend(self, *args, **kwargs):
        raise NotImplementedError()

    def get_default_serializer(self):
        return aiocache.DEFAULT_SERIALIZER()

    def get_default_policy(self):
        return aiocache.DEFAULT_POLICY(self)

    @property
    def serializer(self):
        return self._serializer

    @serializer.setter
    def serializer(self, value):
        self._serializer = value
        new_encoding = getattr(self._serializer, "encoding", 'utf-8')
        self._backend.encoding = new_encoding

    @property
    def policy(self):
        return self._policy

    @policy.setter
    def policy(self, value):
        self._policy = value

    def set_policy(self, class_, *args, **kwargs):
        self._policy = class_(self, *args, **kwargs)

    async def add(self, key, value, ttl=None, dumps_fn=None):  # pragma: no cover
        """
        Stores the value in the given key with ttl if specified. Raises an error if the
        key already exists.
        :param key: str
        :param value: obj
        :param ttl: int the expiration time in seconds
        :param dumps_fn: callable alternative to use as dumps function
        :returns: True if key is inserted
        :raises: Value error if key already exists
        """
        start = time.time()
        dumps = dumps_fn or self._serializer.dumps
        ns_key = self._build_key(key)

        await self._policy.pre_set(key, value)
        await self._backend.add(ns_key, dumps(value), ttl)
        await self._policy.post_set(key, value)

        logger.info("ADD %s %s (%.4f)s", ns_key, True, time.time() - start)
        return True

    async def get(self, key, default=None, loads_fn=None):
        """
        Get a value from the cache. Returns default if not found.
        :param key: str
        :param default: obj to return when key is not found
        :param loads_fn: callable alternative to use as loads function
        :returns: obj loaded
        """
        start = time.time()
        loads = loads_fn or self._serializer.loads
        ns_key = self._build_key(key)

        await self._policy.pre_get(key)
        value = loads(await self._backend.get(ns_key))
        if value:
            await self._policy.post_get(key)

        logger.info("GET %s %s (%.4f)s", ns_key, value is not None, time.time() - start)
        return value or default

    async def multi_get(self, keys, loads_fn=None):
        """
        Get multiple values from the cache, values not found are Nones.

        :param keys: list of str
        :param loads_fn: callable alternative to use as loads function
        :returns: list of objs
        """
        start = time.time()
        loads = loads_fn or self._serializer.loads

        for key in keys:
            await self._policy.pre_get(key)

        ns_keys = [self._build_key(key) for key in keys]
        values = await self._backend.multi_get(ns_keys)
        values = [loads(value) for value in values]

        for key in keys:
            await self._policy.post_get(key)

        logger.info(
            "MULTI_GET %s %d (%.4f)s",
            ns_keys,
            len([value for value in values if value is not None]),
            time.time() - start)
        return values

    async def set(self, key, value, ttl=None, dumps_fn=None):
        """
        Stores the value in the given key with ttl if specified
        :param key: str
        :param value: obj
        :param ttl: int the expiration time in seconds
        :param dumps_fn: callable alternative to use as dumps function
        :returns: True
        """
        start = time.time()
        dumps = dumps_fn or self._serializer.dumps
        ns_key = self._build_key(key)

        await self._policy.pre_set(key, value)
        await self._backend.set(ns_key, dumps(value), ttl)
        await self._policy.post_set(key, value)

        logger.info("SET %s %d (%.4f)s", ns_key, True, time.time() - start)
        return True

    async def multi_set(self, pairs, ttl=None, dumps_fn=None):
        """
        Stores multiple values in the given keys.
        :param pairs: list of two element iterables. First is key and second is value
        :param ttl: int the expiration time of the keys in seconds
        :param dumps_fn: callable alternative to use as dumps function
        :returns: True
        """
        start = time.time()
        dumps = dumps_fn or self._serializer.dumps

        tmp_pairs = []
        for key, value in pairs:
            await self._policy.pre_set(key, value)
            tmp_pairs.append((self._build_key(key), dumps(value)))

        await self._backend.multi_set(tmp_pairs, ttl=ttl)

        for key, value in pairs:
            await self._policy.post_set(key, value)

        logger.info(
            "MULTI_SET %s %d (%.4f)s",
            [key for key, value in tmp_pairs],
            len(pairs),
            time.time() - start)
        return True

    async def delete(self, key):
        """
        Deletes the given key.
        :param key: Key to be deleted
        :returns: int number of deleted keys
        """
        start = time.time()
        ns_key = self._build_key(key)
        ret = await self._backend.delete(ns_key)
        logger.info("DELETE %s %d (%.4f)s", ns_key, ret, time.time() - start)
        return ret

    async def exists(self, key):
        """
        Check key exists in the cache.
        :param key: str key to check
        :returns: True if key exists otherwise False
        """
        start = time.time()
        ns_key = self._build_key(key)
        ret = await self._backend.exists(ns_key)
        logger.info("EXISTS %s %d (%.4f)s", ns_key, ret, time.time() - start)
        return ret

    async def raw(self, command, *args, **kwargs):
        """
        Send the raw command to the underlying client.

        :param command: str with the command.
        :returns: whatever the underlying client returns
        """
        start = time.time()
        ret = await self._backend.raw(command, *args, **kwargs)
        logger.info("%s (%.4f)s", command, time.time() - start)
        return ret

    def _build_key(self, key):
        if self.namespace:
            return "{}{}".format(self.namespace, key)
        return key


class SimpleMemoryCache(BaseCache):
    """
    Cache implementation with the following components as defaults:
        - backend: :class:`aiocache.backends.SimpleMemoryBackend`
        - serializer: :class:`aiocache.serializers.DefaultSerializer`
        - policy: :class:`aiocache.policies.DefaultPolicy`
    """

    def get_backend(self, *args, **kwargs):
        return SimpleMemoryBackend(*args, **kwargs)


class RedisCache(BaseCache):
    """
    Cache implementation with the following components as defaults:
        - backend: :class:`aiocache.backends.RedisBackend`
        - serializer: :class:`aiocache.serializers.DefaultSerializer`
        - policy: :class:`aiocache.policies.DefaultPolicy`
    """

    def get_backend(self, *args, **kwargs):
        return RedisBackend(*args, **kwargs)

    def _build_key(self, key):
        if self.namespace:
            return "{}:{}".format(self.namespace, key)
        return key

    def __repr__(self):  # pragma: no cover
        return "RedisCache ({}:{})".format(self._backend.endpoint, self._backend.port)


class MemcachedCache(BaseCache):
    """
    Cache implementation with the following components as defaults:
        - backend: :class:`aiocache.backends.MemcachedBackend`
        - serializer: :class:`aiocache.serializers.DefaultSerializer`
        - policy: :class:`aiocache.policies.DefaultPolicy`
    """

    def get_backend(self, *args, **kwargs):
        return MemcachedBackend(*args, **kwargs)

    def _build_key(self, key):
        ns_key = super()._build_key(key)
        return str.encode(ns_key)

    def __repr__(self):  # pragma: no cover
        return "MemcachedCache ({}:{})".format(self._backend.endpoint, self._backend.port)
