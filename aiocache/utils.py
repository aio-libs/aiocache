import logging
import aiocache

from aiocache import SimpleMemoryCache
from aiocache.serializers import DefaultSerializer


logger = logging.getLogger(__name__)


def cached(*args, ttl=0, backend=None, serializer=None, **kwargs):
    """
    Caches the functions return value into a key generated with module_name, function_name and args.

    In some cases you will need to send more args than just the ttl, backend and serializer.
    An example would be endpoint and port for the RedisBackend. This extra args will be propagated
    to the backend class when instantiating.

    :param ttl: int seconds to store the function call. Default is 0
    :param backend: backend class to use when calling the ``set``/``get`` operations. Default is
        :class:`aiocache.backends.SimpleMemoryCache`
    :param serializer: serializer instance to use when calling the ``serialize``/``deserialize``.
        Default is :class:`aiocache.serializers.DefaultSerializer`
    """
    cache = get_default_cache(backend=backend, serializer=serializer, *args, **kwargs)

    def cached_decorator(fn):
        async def wrapper(*args, **kwargs):
            key = (fn.__module__ or "stub") + fn.__name__ + str(args) + str(kwargs)
            if await cache.exists(key):
                return await cache.get(key)
            else:
                res = await fn(*args, **kwargs)
                await cache.set(key, res, ttl=ttl)
                return res
        return wrapper
    return cached_decorator


def get_default_cache(*args, backend=None, serializer=None, **kwargs):
    serializer = serializer if serializer else DefaultSerializer()
    if backend:
        return backend(serializer=serializer, *args, **kwargs)
    elif aiocache.default_cache:
        return aiocache.default_cache
    else:
        return SimpleMemoryCache(serializer=serializer, *args, **kwargs)
