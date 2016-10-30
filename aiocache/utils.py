import logging
import aiocache

from aiocache import SimpleMemoryCache
from aiocache.serializers import DefaultSerializer


logger = logging.getLogger(__name__)


def cached(*args, ttl=0, key=None, key_attribute=None, cache=None, serializer=None, **kwargs):
    """
    Caches the functions return value into a key generated with module_name, function_name and args.

    In some cases you will need to send more args than just the ttl, cache and serializer.
    An example would be endpoint and port for the RedisCache. This extra args will be propagated
    to the cache class when instantiating.

    :param ttl: int seconds to store the function call. Default is 0
    :param key: str value to set as key for the function return. Takes precedence over
        key_attribute param.
    :param key_attribute: keyword attribute from the function to use as a key. If not passed,
        it will use module_name + function_name + args + kwargs
    :param cache: cache class to use when calling the ``set``/``get`` operations. Default is
        :class:``aiocache.SimpleMemoryCache``
    :param serializer: serializer instance to use when calling the ``serialize``/``deserialize``.
        Default is :class:``aiocache.serializers.DefaultSerializer``
    """
    cache = get_default_cache(cache=cache, serializer=serializer, *args, **kwargs)

    def cached_decorator(fn):
        async def wrapper(*args, **kwargs):
            cache_key = key or kwargs.get(
                key_attribute, (fn.__module__ or 'stub') + fn.__name__ + str(args) + str(kwargs))
            if await cache.exists(cache_key):
                return await cache.get(cache_key)
            else:
                res = await fn(*args, **kwargs)
                await cache.set(cache_key, res, ttl=ttl)
                return res
        return wrapper
    return cached_decorator


def multi_cached(keys_attribute, cache=None, serializer=None, **kwargs):
    """
    Only supports functions that return dict-like structures. This decorator caches each key/value
    of the dict-like object returned by the function.
    For this decorator to work 100%, the function must follow two prerequisites:
        - It must return a dict-like structure. Each key/value pair in the dict will be cached.
        - It must have a kwarg named ``keys`` that must coincide with the keys that would be
            returned in the response. If its not the case, the call to the function will always
            be done (although the returned values will all be cached).

    :param keys_attribute: str attribute from the function containing an iterable to use
        as keys.
    :param cache: cache class to use when calling the ``set``/``get`` operations. Default is
        :class:`aiocache.SimpleMemoryCache`
    :param serializer: serializer instance to use when calling the ``serialize``/``deserialize``.
        Default is :class:`aiocache.serializers.DefaultSerializer`
    """
    cache = get_default_cache(cache=cache, serializer=serializer, **kwargs)

    def multi_cached_decorator(fn):
        async def wrapper(*args, **kwargs):
            partial_dict = {}
            missing_keys = []
            keys = kwargs[keys_attribute]
            values = await cache.multi_get(keys)
            for key, value in zip(keys, values):
                if value is not None:
                    partial_dict[key] = value
                else:
                    missing_keys.append(key)
            kwargs[keys_attribute] = missing_keys
            if missing_keys:
                partial_dict.update(await fn(*args, **kwargs))
                await cache.multi_set([(key, value) for key, value in partial_dict.items()])
            return partial_dict
        return wrapper
    return multi_cached_decorator


def get_default_cache(*args, cache=None, serializer=None, **kwargs):
    serializer = serializer if serializer else DefaultSerializer()
    if cache:
        return cache(serializer=serializer, *args, **kwargs)
    elif hasattr(aiocache, 'default_cache'):
        return aiocache.default_cache
    else:
        return SimpleMemoryCache(serializer=serializer, *args, **kwargs)
