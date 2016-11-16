import time

from async_timeout import timeout as Timeout

import aiocache

from aiocache.log import logger
from aiocache.backends import SimpleMemoryBackend, RedisBackend, MemcachedBackend


class BaseCache:
    """
    Base class that agregates the common logic for the different caches that may exist. Cache
    related available options are:

    :param serializer: obj with :class:`aiocache.serializers.DefaultSerializer` interface.
    :param policy: obj with :class:`aiocache.policies.DefaultPolicy` interface.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend.
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.
    """

    def __init__(self, serializer=None, policy=None, namespace=None, timeout=5):
        self._timeout = timeout
        self.namespace = namespace if namespace is not None else \
            aiocache.settings.DEFAULT_CACHE_KWARGS.get("namespace")
        self.encoding = "utf-8"

        self._serializer = None
        self.serializer = serializer or self.get_default_serializer()

        self._policy = None
        self.policy = policy or self.get_default_policy()

    def get_default_serializer(self):
        return aiocache.settings.DEFAULT_SERIALIZER()

    def get_default_policy(self):
        return aiocache.settings.DEFAULT_POLICY()

    @property
    def serializer(self):
        return self._serializer

    @serializer.setter
    def serializer(self, value):
        self._serializer = value
        new_encoding = getattr(self._serializer, "encoding", 'utf-8')
        self.encoding = new_encoding

    @property
    def policy(self):
        return self._policy

    @policy.setter
    def policy(self, value):
        self._policy = value

    async def add(self, key, value, ttl=None, dumps_fn=None, namespace=None):
        """
        Stores the value in the given key with ttl if specified. Raises an error if the
        key already exists.

        :param key: str
        :param value: obj
        :param ttl: int the expiration time in seconds
        :param dumps_fn: callable alternative to use as dumps function
        :param namespace: str alternative namespace to use
        :returns: True if key is inserted
        :raises:
            - ValueError if key already exists
            - :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        with Timeout(self._timeout):
            start = time.time()
            dumps = dumps_fn or self._serializer.dumps
            ns_key = self._build_key(key, namespace=namespace)

            await self._policy.pre_set(self, key, value)
            await self._add(ns_key, dumps(value), ttl)
            await self._policy.post_set(self, key, value)

            logger.info("ADD %s %s (%.4f)s", ns_key, True, time.time() - start)
            return True

    async def _add(self, key, value, ttl):
        pass

    async def get(self, key, default=None, loads_fn=None, namespace=None):
        """
        Get a value from the cache. Returns default if not found.

        :param key: str
        :param default: obj to return when key is not found
        :param loads_fn: callable alternative to use as loads function
        :param namespace: str alternative namespace to use
        :returns: obj loaded
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        with Timeout(self._timeout):
            start = time.time()
            loads = loads_fn or self._serializer.loads
            ns_key = self._build_key(key, namespace=namespace)

            await self._policy.pre_get(self, key)
            value = loads(await self._get(ns_key))
            if value:
                await self._policy.post_get(self, key)

            logger.info("GET %s %s (%.4f)s", ns_key, value is not None, time.time() - start)
            return value or default

    async def _get(self, key, default):
        pass

    async def multi_get(self, keys, loads_fn=None, namespace=None):
        """
        Get multiple values from the cache, values not found are Nones.

        :param keys: list of str
        :param loads_fn: callable alternative to use as loads function
        :param namespace: str alternative namespace to use
        :returns: list of objs
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        with Timeout(self._timeout):
            start = time.time()
            loads = loads_fn or self._serializer.loads

            for key in keys:
                await self._policy.pre_get(self, key)

            ns_keys = [self._build_key(key, namespace=namespace) for key in keys]
            values = [loads(value) for value in await self._multi_get(ns_keys)]

            for key in keys:
                await self._policy.post_get(self, key)

            logger.info(
                "MULTI_GET %s %d (%.4f)s",
                ns_keys,
                len([value for value in values if value is not None]),
                time.time() - start)
            return values

    async def _multi_get(self, keys, loads_fn):
        pass

    async def set(self, key, value, ttl=None, dumps_fn=None, namespace=None):
        """
        Stores the value in the given key with ttl if specified

        :param key: str
        :param value: obj
        :param ttl: int the expiration time in seconds
        :param dumps_fn: callable alternative to use as dumps function
        :param namespace: str alternative namespace to use
        :returns: True
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        with Timeout(self._timeout):
            start = time.time()
            dumps = dumps_fn or self._serializer.dumps
            ns_key = self._build_key(key, namespace=namespace)

            await self._policy.pre_set(self, key, value)
            await self._set(ns_key, dumps(value), ttl)
            await self._policy.post_set(self, key, value)

            logger.info("SET %s %d (%.4f)s", ns_key, True, time.time() - start)
            return True

    async def _set(self, key, value, ttl):
        pass

    async def multi_set(self, pairs, ttl=None, dumps_fn=None, namespace=None):
        """
        Stores multiple values in the given keys.

        :param pairs: list of two element iterables. First is key and second is value
        :param ttl: int the expiration time of the keys in seconds
        :param dumps_fn: callable alternative to use as dumps function
        :param namespace: str alternative namespace to use
        :returns: True
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        with Timeout(self._timeout):
            start = time.time()
            dumps = dumps_fn or self._serializer.dumps

            tmp_pairs = []
            for key, value in pairs:
                await self._policy.pre_set(self, key, value)
                tmp_pairs.append((self._build_key(key, namespace=namespace), dumps(value)))

            await self._multi_set(tmp_pairs, ttl=ttl)

            for key, value in pairs:
                await self._policy.post_set(self, key, value)

            logger.info(
                "MULTI_SET %s %d (%.4f)s",
                [key for key, value in tmp_pairs],
                len(pairs),
                time.time() - start)
            return True

    async def _multi_set(self, pairs, ttl):
        pass

    async def delete(self, key, namespace=None):
        """
        Deletes the given key.

        :param key: Key to be deleted
        :param namespace: str alternative namespace to use
        :returns: int number of deleted keys
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        with Timeout(self._timeout):
            start = time.time()
            ns_key = self._build_key(key, namespace=namespace)
            ret = await self._delete(ns_key)
            logger.info("DELETE %s %d (%.4f)s", ns_key, ret, time.time() - start)
            return ret

    async def _delete(self, key):
        pass

    async def exists(self, key, namespace=None):
        """
        Check key exists in the cache.

        :param key: str key to check
        :param namespace: str alternative namespace to use
        :returns: True if key exists otherwise False
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        with Timeout(self._timeout):
            start = time.time()
            ns_key = self._build_key(key, namespace=namespace)
            ret = await self._exists(ns_key)
            logger.info("EXISTS %s %d (%.4f)s", ns_key, ret, time.time() - start)
            return ret

    async def _exists(self, key):
        pass

    async def clear(self, namespace=None):
        """
        Clears the cache in the cache namespace. If an alternative namespace is given, it will
        clear those ones instead.

        :param namespace: str alternative namespace to use
        :returns: True
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        with Timeout(self._timeout):
            start = time.time()
            ret = await self._clear(namespace)
            logger.info("CLEAR %s %d (%.4f)s", namespace, ret, time.time() - start)
            return ret

    async def _clear(self):
        pass

    async def raw(self, command, *args, **kwargs):
        """
        Send the raw command to the underlying client.

        :param command: str with the command.
        :returns: whatever the underlying client returns
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        with Timeout(self._timeout):
            start = time.time()
            ret = await self._raw(command, *args, **kwargs)
            logger.info("%s (%.4f)s", command, time.time() - start)
            return ret

    async def _raw(self, command, *args, **kwargs):
        pass

    def _build_key(self, key, namespace=None):
        if namespace is not None:
            return "{}{}".format(namespace, key)
        if self.namespace is not None:
            return "{}{}".format(self.namespace, key)
        return key


class SimpleMemoryCache(SimpleMemoryBackend, BaseCache):
    """
    :class:`aiocache.backends.SimpleMemoryBackend` cache implementation with
    the following components as defaults:
        - serializer: :class:`aiocache.serializers.DefaultSerializer`
        - policy: :class:`aiocache.policies.DefaultPolicy`

    Config options are:

    :param serializer: obj with :class:`aiocache.serializers.DefaultSerializer` interface.
    :param policy: obj with :class:`aiocache.policies.DefaultPolicy` interface.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend.
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class RedisCache(RedisBackend, BaseCache):
    """
    :class:`aiocache.backends.RedisBackend` cache implementation with the
    following components as defaults:
        - serializer: :class:`aiocache.serializers.DefaultSerializer`
        - policy: :class:`aiocache.policies.DefaultPolicy`

    Config options are:

    :param serializer: obj with :class:`aiocache.serializers.DefaultSerializer` interface.
    :param policy: obj with :class:`aiocache.policies.DefaultPolicy` interface.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend.
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.
    :param endpoint: str with the endpoint to connect to
    :param port: int with the port to connect to
    :param db: int indicating database to use
    :param password: str indicating password to use
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _build_key(self, key, namespace=None):
        if namespace is not None:
            return "{}{}{}".format(namespace, ":" if namespace else "", key)
        if self.namespace is not None:
            return "{}{}{}".format(self.namespace, ":" if self.namespace else "", key)
        return key

    def __repr__(self):  # pragma: no cover
        return "RedisCache ({}:{})".format(self.endpoint, self.port)


class MemcachedCache(MemcachedBackend, BaseCache):
    """
    :class:`aiocache.backends.MemcachedCache` cache implementation with the following
    components as defaults:
        - serializer: :class:`aiocache.serializers.DefaultSerializer`
        - policy: :class:`aiocache.policies.DefaultPolicy`

    Config options are:

    :param serializer: obj with :class:`aiocache.serializers.DefaultSerializer` interface.
    :param policy: obj with :class:`aiocache.policies.DefaultPolicy` interface.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend.
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.
    :param endpoint: str with the endpoint to connect to
    :param port: int with the port to connect to
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _build_key(self, key, namespace=None):
        ns_key = super()._build_key(key, namespace=namespace)
        return str.encode(ns_key)

    def __repr__(self):  # pragma: no cover
        return "MemcachedCache ({}:{})".format(self.endpoint, self.port)
