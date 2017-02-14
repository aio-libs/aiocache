from aiocache.log import logger
from aiocache.utils import get_args_dict, get_cache


def cached(
        ttl=0, key=None, key_from_attr=None, cache=None, serializer=None, plugins=None, **kwargs):
    """
    Caches the functions return value into a key generated with module_name, function_name and args.

    In some cases you will need to send more args to configure the cache object.
    An example would be endpoint and port for the RedisCache. You can send those args as
    kwargs and they will be propagated accordingly.

    :param ttl: int seconds to store the function call. Default is 0 which means no expiration.
    :param key: str value to set as key for the function return. Takes precedence over
        key_from_attr param. If key and key_from_attr are not passed, it will use module_name
        + function_name + args + kwargs
    :param key_from_attr: arg or kwarg name from the function to use as a key.
    :param cache: cache class to use when calling the ``set``/``get`` operations.
        Default is the one configured in ``aiocache.settings.DEFAULT_CACHE``
    :param serializer: serializer instance to use when calling the ``dumps``/``loads``.
        Default is the one configured in ``aiocache.settings.DEFAULT_SERIALIZER``
    :param plugins: plugins to use when calling the cmd hooks
        Default is the one configured in ``aiocache.settings.DEFAULT_PLUGINS``
    """
    cache_kwargs = kwargs

    def cached_decorator(func):
        async def wrapper(*args, **kwargs):
            cache_instance = get_cache(
                cache=cache, serializer=serializer, plugins=plugins, **cache_kwargs)
            args_dict = get_args_dict(func, args, kwargs)
            cache_key = key or args_dict.get(
                key_from_attr,
                (func.__module__ or 'stub') + func.__name__ + str(args) + str(kwargs))

            try:
                if await cache_instance.exists(cache_key):
                    return await cache_instance.get(cache_key)

            except Exception:
                logger.exception("Unexpected error with %s", cache_instance)

            result = await func(*args, **kwargs)

            try:
                await cache_instance.set(cache_key, result, ttl=ttl)
            except Exception:
                logger.exception("Unexpected error with %s", cache_instance)

            return result

        return wrapper
    return cached_decorator


def multi_cached(
        keys_from_attr, key_builder=None, ttl=0, cache=None,
        serializer=None, plugins=None, **kwargs):
    """
    Only supports functions that return dict-like structures. This decorator caches each key/value
    of the dict-like object returned by the function.

    If key_builder is passed, before storing the key, it will be transformed according to the output
    of the function.

    If the attribute specified to be the key is an empty list, the cache will be ignored and
    the function will be called as expected.

    :param keys_from_attr: arg or kwarg name from the function containing an iterable to use
        as keys to index in the cache.
    :param key_builder: Callable that allows to change the format of the keys before storing.
        Receives a dict with all the args of the function.
    :param ttl: int seconds to store the keys. Default is 0 which means no expiration.
    :param cache: cache class to use when calling the ``multi_set``/``multi_get`` operations.
        Default is the one configured in ``aiocache.settings.DEFAULT_CACHE``
    :param serializer: serializer instance to use when calling the ``dumps``/``loads``.
        Default is the one configured in ``aiocache.settings.DEFAULT_SERIALIZER``
    :param plugins: plugins to use when calling the cmd hooks
        Default is the one configured in ``aiocache.settings.DEFAULT_PLUGINS``
    """
    key_builder = key_builder or (lambda x, args_dict: x)
    cache_kwargs = kwargs

    def multi_cached_decorator(func):
        async def wrapper(*args, **kwargs):
            cache_instance = get_cache(
                cache=cache, serializer=serializer, plugins=plugins, **cache_kwargs)
            partial_result = {}
            args_dict = get_args_dict(func, args, kwargs)
            keys = args_dict[keys_from_attr]
            cache_keys = [key_builder(key, args_dict) for key in keys]

            result = None
            missing_keys = "all"
            if len(keys) > 0:
                missing_keys = []
                try:
                    values = await cache_instance.multi_get(cache_keys)
                    for key, value in zip(keys, values):
                        if value is not None:
                            partial_result[key] = value
                        else:
                            missing_keys.append(key)
                    args_dict[keys_from_attr] = missing_keys

                except Exception:
                    logger.exception("Unexpected error with %s", cache_instance)
                    missing_keys = "all"

            if missing_keys:
                result = await func(**args_dict)
                if result:
                    partial_result.update(result)
                    try:
                        await cache_instance.multi_set(
                            [(key_builder(
                                key, args_dict), value) for key, value in result.items()],
                            ttl=ttl)
                    except Exception:
                        logger.exception("Unexpected error with %s", cache_instance)

            return partial_result

        return wrapper
    return multi_cached_decorator
