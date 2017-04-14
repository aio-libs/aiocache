from aiocache import settings


def get_cache(cache=None, serializer=None, plugins=None, **kwargs):
    cache = cache or settings.get_cache_class()
    serializer = serializer
    plugins = plugins

    instance = cache(
        serializer=serializer,
        plugins=plugins,
        **{**settings.get_cache_args(), **kwargs})
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
    new_value = from_fallback
    if value is not None:
        new_value = value
    elif cls and issubclass(settings.get_cache_class(), cls):
        new_value = settings.get_cache_args().get(from_config, new_value)

    return new_value
