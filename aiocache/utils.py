import inspect

import aiocache


def get_args_dict(fn, args, kwargs):
    defaults = {
        arg_name: arg.default for arg_name, arg in inspect.signature(fn).parameters.items()
        if arg.default is not inspect._empty
    }
    args_names = fn.__code__.co_varnames[:fn.__code__.co_argcount]
    return {**defaults, **dict(zip(args_names, args)), **kwargs}


def cached(ttl=0, key=None, key_attribute=None, cache=None, serializer=None, **kwargs):
    """
    Caches the functions return value into a key generated with module_name, function_name and args.

    In some cases you will need to send more args than just the ttl, cache and serializer.
    An example would be endpoint and port for the RedisCache. This extra args will be propagated
    to the cache class when instantiating.

    :param ttl: int seconds to store the function call. Default is 0
    :param key: str value to set as key for the function return. Takes precedence over
        key_attribute param.
    :param key_attribute: arg or kwarg name from the function to use as a key. If not passed,
        it will use module_name + function_name + args + kwargs
    :param cache: cache class to use when calling the ``set``/``get`` operations. Default is
        :class:``aiocache.SimpleMemoryCache``
    :param serializer: serializer instance to use when calling the ``serialize``/``deserialize``.
        Default is :class:``aiocache.serializers.DefaultSerializer``
    """
    cache = get_cache(cache=cache, serializer=serializer, **kwargs)

    def cached_decorator(fn):
        async def wrapper(*args, **kwargs):
            args_dict = get_args_dict(fn, args, kwargs)
            cache_key = key or args_dict.get(
                key_attribute, (fn.__module__ or 'stub') + fn.__name__ + str(args) + str(kwargs))
            if await cache.exists(cache_key):
                return await cache.get(cache_key)
            else:
                res = await fn(*args, **kwargs)
                await cache.set(cache_key, res, ttl=ttl)
                return res
        return wrapper
    return cached_decorator


def multi_cached(keys_attribute, key_builder=None, ttl=0, cache=None, serializer=None, **kwargs):
    """
    Only supports functions that return dict-like structures. This decorator caches each key/value
    of the dict-like object returned by the function.

    The decorated function must return a dict-like structure. Each key/value pair in the dict
    will be cached. If key_builder is passed, before storing the key will be transformed
    according to the output of the function

    If the attribute specified to be the key is empty, the cache will be ignored and the function
    will be called as expected.

    :param keys_attribute: arg or kwarg name from the function containing an iterable to use
        as keys.
    :param key_builder: Callable that allows to change the format of the keys before storing.
        Receives a dict with all the args of the function.
    :param ttl: int seconds to store the keys. Default is 0
    :param cache: cache class to use when calling the ``set``/``get`` operations. Default is
        :class:`aiocache.SimpleMemoryCache`
    :param serializer: serializer instance to use when calling the ``serialize``/``deserialize``.
        Default is :class:`aiocache.serializers.DefaultSerializer`
    """
    cache = get_cache(cache=cache, serializer=serializer, **kwargs)
    key_builder = key_builder or (lambda x, args_dict: x)

    def multi_cached_decorator(fn):
        async def wrapper(*args, **kwargs):
            partial_result = {}
            args_dict = get_args_dict(fn, args, kwargs)
            keys = args_dict[keys_attribute]
            cache_keys = [key_builder(key, args_dict) for key in keys]

            if len(keys) > 0:
                missing_keys = []
                values = await cache.multi_get(cache_keys)
                for key, value in zip(keys, values):
                    if value is not None:
                        partial_result[key] = value
                    else:
                        missing_keys.append(key)
                args_dict[keys_attribute] = missing_keys
            else:
                missing_keys = "all"

            if missing_keys:
                partial_result.update(await fn(**args_dict))
                if partial_result:
                    await cache.multi_set(
                        [(key_builder(
                            key, args_dict), value) for key, value in partial_result.items()],
                        ttl=ttl)

            return partial_result

        return wrapper
    return multi_cached_decorator


def get_cache(cache=None, serializer=None, policy=None, namespace=None, **kwargs):
    cache = cache or aiocache.DEFAULT_CACHE
    serializer = serializer or aiocache.DEFAULT_SERIALIZER()
    policy = policy or aiocache.DEFAULT_POLICY
    namespace = namespace or aiocache.DEFAULT_NAMESPACE

    c = cache(namespace=namespace, serializer=serializer, **{**aiocache.DEFAULT_KWARGS, **kwargs})
    c.set_policy(policy)
    return c
