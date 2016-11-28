import inspect

import aiocache

from aiocache.log import logger


def class_from_string(class_path):
    class_name = class_path.split('.')[-1]
    module_name = class_path.rstrip(class_name).rstrip(".")
    return getattr(__import__(module_name, fromlist=[class_name]), class_name)


def get_args_dict(func, args, kwargs):
    defaults = {
        arg_name: arg.default for arg_name, arg in inspect.signature(func).parameters.items()
        if arg.default is not inspect._empty
    }
    args_names = func.__code__.co_varnames[:func.__code__.co_argcount]
    return {**defaults, **dict(zip(args_names, args)), **kwargs}


def cached(
        ttl=0, key=None, key_from_attr=None, cache=None, serializer=None, plugins=None, **kwargs):
    """
    Caches the functions return value into a key generated with module_name, function_name and args.

    In some cases you will need to send more args to configure the cache object.
    An example would be endpoint and port for the RedisCache. You can send those args as
    kwargs and they will be propagated accordingly.

    :param ttl: int seconds to store the function call. Default is 0
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
    cache = get_cache(cache=cache, serializer=serializer, plugins=plugins, **kwargs)

    def cached_decorator(func):
        async def wrapper(*args, **kwargs):
            args_dict = get_args_dict(func, args, kwargs)
            cache_key = key or args_dict.get(
                key_from_attr,
                (func.__module__ or 'stub') + func.__name__ + str(args) + str(kwargs))

            try:
                if await cache.exists(cache_key):
                    return await cache.get(cache_key)

            except Exception:
                logger.exception("Unexpected error with %s", cache)

            result = await func(*args, **kwargs)

            try:
                await cache.set(cache_key, result, ttl=ttl)
            except Exception:
                logger.exception("Unexpected error with %s", cache)

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
    :param ttl: int seconds to store the keys. Default is 0
    :param cache: cache class to use when calling the ``multi_set``/``multi_get`` operations.
        Default is the one configured in ``aiocache.settings.DEFAULT_CACHE``
    :param serializer: serializer instance to use when calling the ``dumps``/``loads``.
        Default is the one configured in ``aiocache.settings.DEFAULT_SERIALIZER``
    :param plugins: plugins to use when calling the cmd hooks
        Default is the one configured in ``aiocache.settings.DEFAULT_PLUGINS``
    """
    cache = get_cache(cache=cache, serializer=serializer, plugins=plugins, **kwargs)
    key_builder = key_builder or (lambda x, args_dict: x)

    def multi_cached_decorator(func):
        async def wrapper(*args, **kwargs):
            partial_result = {}
            args_dict = get_args_dict(func, args, kwargs)
            keys = args_dict[keys_from_attr]
            cache_keys = [key_builder(key, args_dict) for key in keys]

            result = None
            missing_keys = "all"
            if len(keys) > 0:
                missing_keys = []
                try:
                    values = await cache.multi_get(cache_keys)
                    for key, value in zip(keys, values):
                        if value is not None:
                            partial_result[key] = value
                        else:
                            missing_keys.append(key)
                    args_dict[keys_from_attr] = missing_keys

                except Exception:
                    logger.exception("Unexpected error with %s", cache)
                    missing_keys = "all"

            if missing_keys:
                result = await func(**args_dict)
                partial_result.update(result)
                if partial_result:
                    try:
                        await cache.multi_set(
                            [(key_builder(
                                key, args_dict), value) for key, value in partial_result.items()],
                            ttl=ttl)
                    except Exception:
                        logger.exception("Unexpected error with %s", cache)

            return partial_result

        return wrapper
    return multi_cached_decorator


def get_cache(cache=None, serializer=None, plugins=None, **kwargs):
    cache = cache or aiocache.settings.DEFAULT_CACHE
    serializer = serializer
    plugins = plugins

    instance = cache(
        serializer=serializer,
        plugins=plugins,
        **{**aiocache.settings.DEFAULT_CACHE_KWARGS, **kwargs})
    return instance
