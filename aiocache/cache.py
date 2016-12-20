import time

from async_timeout import timeout as Timeout

import aiocache

from aiocache.log import logger
from aiocache.backends import SimpleMemoryBackend, RedisBackend, MemcachedBackend
from aiocache.plugins import plugin_pipeline


class BaseCache:
    """
    Base class that agregates the common logic for the different caches that may exist. Cache
    related available options are:

    :param serializer: obj with :class:`aiocache.serializers.DefaultSerializer` interface.
    :param plugins: list of :class:`aiocache.plugins.BasePlugin` derived classes.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend.
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.
    """

    def __init__(self, serializer=None, plugins=None, namespace=None, timeout=5):
        self._timeout = timeout
        self.namespace = namespace if namespace is not None else \
            aiocache.settings.DEFAULT_CACHE_KWARGS.get("namespace")
        self.encoding = "utf-8"

        self._serializer = None
        self.serializer = serializer or self.get_default_serializer()

        self._plugins = None
        self.plugins = plugins or self.get_default_plugins()

    def get_default_serializer(self):
        return aiocache.settings.DEFAULT_SERIALIZER()

    def get_default_plugins(self):
        return [plugin(**config) for plugin, config in aiocache.settings.DEFAULT_PLUGINS.items()]

    @property
    def serializer(self):
        return self._serializer

    @serializer.setter
    def serializer(self, value):
        self._serializer = value
        self.encoding = getattr(self._serializer, "encoding", 'utf-8')

    @property
    def plugins(self):
        return self._plugins

    @plugins.setter
    def plugins(self, value):
        self._plugins = value

    @plugin_pipeline
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

            await self._add(ns_key, dumps(value), ttl)

            logger.debug("ADD %s %s (%.4f)s", ns_key, True, time.time() - start)
            return True

    async def _add(self, key, value, ttl):
        raise NotImplementedError()

    @plugin_pipeline
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

            value = loads(await self._get(ns_key))

            logger.debug("GET %s %s (%.4f)s", ns_key, value is not None, time.time() - start)
            return value or default

    async def _get(self, key):
        raise NotImplementedError()

    @plugin_pipeline
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

            ns_keys = [self._build_key(key, namespace=namespace) for key in keys]
            values = [loads(value) for value in await self._multi_get(ns_keys)]

            logger.debug(
                "MULTI_GET %s %d (%.4f)s",
                ns_keys,
                len([value for value in values if value is not None]),
                time.time() - start)
            return values

    async def _multi_get(self, keys):
        raise NotImplementedError()

    @plugin_pipeline
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

            await self._set(ns_key, dumps(value), ttl)

            logger.debug("SET %s %d (%.4f)s", ns_key, True, time.time() - start)
            return True

    async def _set(self, key, value, ttl):
        raise NotImplementedError()

    @plugin_pipeline
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
                tmp_pairs.append((self._build_key(key, namespace=namespace), dumps(value)))

            await self._multi_set(tmp_pairs, ttl=ttl)

            logger.debug(
                "MULTI_SET %s %d (%.4f)s",
                [key for key, value in tmp_pairs],
                len(pairs),
                time.time() - start)
            return True

    async def _multi_set(self, pairs, ttl):
        raise NotImplementedError()

    @plugin_pipeline
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
            logger.debug("DELETE %s %d (%.4f)s", ns_key, ret, time.time() - start)
            return ret

    async def _delete(self, key):
        raise NotImplementedError()

    @plugin_pipeline
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
            logger.debug("EXISTS %s %d (%.4f)s", ns_key, ret, time.time() - start)
            return ret

    async def _exists(self, key):
        raise NotImplementedError()

    @plugin_pipeline
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
            logger.debug("CLEAR %s %d (%.4f)s", namespace, ret, time.time() - start)
            return ret

    async def _clear(self, namespace):
        raise NotImplementedError()

    @plugin_pipeline
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
            logger.debug("%s (%.4f)s", command, time.time() - start)
            return ret

    async def _raw(self, command, *args, **kwargs):
        raise NotImplementedError()

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
      - plugins: None

    Config options are:

    :param serializer: obj with :class:`aiocache.serializers.DefaultSerializer` interface.
    :param plugins: list of :class:`aiocache.plugins.BasePlugin` derived classes.
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
      - plugins: None

    Config options are:

    :param serializer: obj with :class:`aiocache.serializers.DefaultSerializer` interface.
    :param plugins: list of :class:`aiocache.plugins.BasePlugin` derived classes.
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
      - plugins: None

    Config options are:

    :param serializer: obj with :class:`aiocache.serializers.DefaultSerializer` interface.
    :param plugins: list of :class:`aiocache.plugins.BasePlugin` derived classes.
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
