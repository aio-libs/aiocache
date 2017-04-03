import inspect

import aiocache


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


def get_cache(cache=None, serializer=None, plugins=None, **kwargs):
    cache = cache or aiocache.settings.DEFAULT_CACHE
    serializer = serializer
    plugins = plugins

    instance = cache(
        serializer=serializer,
        plugins=plugins,
        **{**aiocache.settings.DEFAULT_CACHE_KWARGS, **kwargs})
    return instance


def get_cache_value_with_fallbacks(value, from_config, from_fallback, cls=None):
    """
    Given a value, decide wether to use the original one, the config or the default one.
    Priority applies as follows:
        - original if its not None
        - from_config if its not None and the cls coincides with the default cache
        - default value
    :param value: original value.
    :param from_config: str name of the field to retrieve from DEFAULT_CACHE_KWARGS.
    :param from_fallback: fallback value to apply in case none of the previous applied.
    :param cls: class of the caller to match with DEFAULT_CACHE.
    """
    v = from_fallback
    if value is not None:
        v = value
    elif cls and issubclass(aiocache.settings.DEFAULT_CACHE, cls):
        v = aiocache.settings.DEFAULT_CACHE_KWARGS.get(from_config, v)

    return v
