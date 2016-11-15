import time
import asyncio

import aiocache

from aiocache.log import logger
from aiocache.backends import SimpleMemoryBackend, RedisBackend, MemcachedBackend


class BaseCache:
    """
    Base class that agregates the common logic for the different caches that may exist. Cache
    related available options are:

    :param serializer: obj with :class:`aiocache.serializers.BaseSerializer` interface.
        Must implement ``loads`` and ``dumps`` methods.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend.
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.

    In case you need to pass extra information to the underlying backend, pass it as extra kwargs.
    """

    def __init__(self, serializer=None, policy=None, namespace=None, timeout=5, **kwargs):

        self._timeout = timeout
        self.namespace = namespace if namespace is not None else \
            aiocache.settings.DEFAULT_CACHE_KWARGS.get("namespace")
        self._backend = self.get_backend(**{**aiocache.settings.DEFAULT_CACHE_KWARGS, **kwargs})
        self.serializer = serializer or self.get_default_serializer()
        self.policy = policy or self.get_default_policy()

    def get_backend(self, *args, **kwargs):
        raise NotImplementedError()

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
        self._backend.encoding = new_encoding

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
        return await asyncio.wait_for(
            self._add(key, value, ttl, dumps_fn, namespace), timeout=self._timeout)

    async def _add(self, key, value, ttl, dumps_fn, namespace):
        start = time.time()
        dumps = dumps_fn or self._serializer.dumps
        ns_key = self._build_key(key, namespace=namespace)

        await self._policy.pre_set(self, key, value)
        await self._backend.add(ns_key, dumps(value), ttl)
        await self._policy.post_set(self, key, value)

        logger.info("ADD %s %s (%.4f)s", ns_key, True, time.time() - start)
        return True

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
        return await asyncio.wait_for(
            self._get(key, default, loads_fn, namespace), timeout=self._timeout)

    async def _get(self, key, default, loads_fn, namespace):
        start = time.time()
        loads = loads_fn or self._serializer.loads
        ns_key = self._build_key(key, namespace=namespace)

        await self._policy.pre_get(self, key)
        value = loads(await self._backend.get(ns_key))
        if value:
            await self._policy.post_get(self, key)

        logger.info("GET %s %s (%.4f)s", ns_key, value is not None, time.time() - start)
        return value or default

    async def multi_get(self, keys, loads_fn=None, namespace=None):
        """
        Get multiple values from the cache, values not found are Nones.

        :param keys: list of str
        :param loads_fn: callable alternative to use as loads function
        :param namespace: str alternative namespace to use
        :returns: list of objs
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        return await asyncio.wait_for(
            self._multi_get(keys, loads_fn, namespace), timeout=self._timeout)

    async def _multi_get(self, keys, loads_fn, namespace):
        start = time.time()
        loads = loads_fn or self._serializer.loads

        for key in keys:
            await self._policy.pre_get(self, key)

        ns_keys = [self._build_key(key, namespace=namespace) for key in keys]
        values = [loads(value) for value in await self._backend.multi_get(ns_keys)]

        for key in keys:
            await self._policy.post_get(self, key)

        logger.info(
            "MULTI_GET %s %d (%.4f)s",
            ns_keys,
            len([value for value in values if value is not None]),
            time.time() - start)
        return values

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
        return await asyncio.wait_for(
            self._set(key, value, ttl, dumps_fn, namespace), timeout=self._timeout)

    async def _set(self, key, value, ttl, dumps_fn, namespace):
        start = time.time()
        dumps = dumps_fn or self._serializer.dumps
        ns_key = self._build_key(key, namespace=namespace)

        await self._policy.pre_set(self, key, value)
        await self._backend.set(ns_key, dumps(value), ttl)
        await self._policy.post_set(self, key, value)

        logger.info("SET %s %d (%.4f)s", ns_key, True, time.time() - start)
        return True

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
        return await asyncio.wait_for(
            self._multi_set(pairs, ttl, dumps_fn, namespace), timeout=self._timeout)

    async def _multi_set(self, pairs, ttl, dumps_fn, namespace):
        start = time.time()
        dumps = dumps_fn or self._serializer.dumps

        tmp_pairs = []
        for key, value in pairs:
            await self._policy.pre_set(self, key, value)
            tmp_pairs.append((self._build_key(key, namespace=namespace), dumps(value)))

        await self._backend.multi_set(tmp_pairs, ttl=ttl)

        for key, value in pairs:
            await self._policy.post_set(self, key, value)

        logger.info(
            "MULTI_SET %s %d (%.4f)s",
            [key for key, value in tmp_pairs],
            len(pairs),
            time.time() - start)
        return True

    async def delete(self, key, namespace=None):
        """
        Deletes the given key.

        :param key: Key to be deleted
        :param namespace: str alternative namespace to use
        :returns: int number of deleted keys
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        return await asyncio.wait_for(self._delete(key, namespace), timeout=self._timeout)

    async def _delete(self, key, namespace):
        start = time.time()
        ns_key = self._build_key(key, namespace=namespace)
        ret = await self._backend.delete(ns_key)
        logger.info("DELETE %s %d (%.4f)s", ns_key, ret, time.time() - start)
        return ret

    async def exists(self, key, namespace=None):
        """
        Check key exists in the cache.

        :param key: str key to check
        :param namespace: str alternative namespace to use
        :returns: True if key exists otherwise False
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        return await asyncio.wait_for(self._exists(key, namespace), timeout=self._timeout)

    async def _exists(self, key, namespace):
        start = time.time()
        ns_key = self._build_key(key, namespace=namespace)
        ret = await self._backend.exists(ns_key)
        logger.info("EXISTS %s %d (%.4f)s", ns_key, ret, time.time() - start)
        return ret

    async def clear(self, namespace=None):
        """
        Clears the cache in the cache namespace. If an alternative namespace is given, it will
        clear those ones instead.

        :param namespace: str alternative namespace to use
        :returns: True
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        return await asyncio.wait_for(self._clear(namespace), timeout=self._timeout)

    async def _clear(self, namespace):
        start = time.time()
        ret = await self._backend.clear(namespace)
        logger.info("CLEAR %s %d (%.4f)s", namespace, ret, time.time() - start)
        return ret

    async def raw(self, command, *args, **kwargs):
        """
        Send the raw command to the underlying client.

        :param command: str with the command.
        :returns: whatever the underlying client returns
        :raises: :class:`asyncio.TimeoutError` if it lasts more than self._timeout
        """
        return await asyncio.wait_for(
            self._raw(command, *args, **kwargs), timeout=self._timeout)

    async def _raw(self, command, *args, **kwargs):
        start = time.time()
        ret = await self._backend.raw(command, *args, **kwargs)
        logger.info("%s (%.4f)s", command, time.time() - start)
        return ret

    def _build_key(self, key, namespace=None):
        if namespace is not None:
            return "{}{}".format(namespace, key)
        if self.namespace is not None:
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

    def _build_key(self, key, namespace=None):
        if namespace is not None:
            return "{}{}{}".format(namespace, ":" if namespace else "", key)
        if self.namespace is not None:
            return "{}{}{}".format(self.namespace, ":" if self.namespace else "", key)
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

    def _build_key(self, key, namespace=None):
        ns_key = super()._build_key(key, namespace=namespace)
        return str.encode(ns_key)

    def __repr__(self):  # pragma: no cover
        return "MemcachedCache ({}:{})".format(self._backend.endpoint, self._backend.port)
