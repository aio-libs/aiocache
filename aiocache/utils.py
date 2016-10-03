import logging
import aiocache

from aiocache import SimpleMemoryCache
from aiocache.serializers import DefaultSerializer


logger = logging.getLogger(__name__)


def cached(ttl=0, backend=None, serializer=None, *args, **kwargs):
    cache = get_default_cache(backend=backend, serializer=serializer, *args, **kwargs)

    def cached_decorator(fn):
        async def wrapper(*args, **kwargs):
            key = fn.__module__ + fn.__name__ + str(args) + str(kwargs)
            value = await cache.get(key)
            if value:
                return value
            else:
                res = await fn(*args, **kwargs)
                await cache.set(key, res, ttl=ttl)
                return res
        return wrapper
    return cached_decorator


def get_default_cache(backend=None, serializer=None, *args, **kwargs):
    serializer = serializer if serializer else DefaultSerializer()
    if backend:
        return backend(serializer=serializer, *args, **kwargs)
    elif aiocache.default_cache:
        return aiocache.default_cache
    else:
        return SimpleMemoryCache(serializer=serializer, *args, **kwargs)
