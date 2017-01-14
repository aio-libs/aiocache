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
