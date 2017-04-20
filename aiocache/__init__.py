from copy import deepcopy

from aiocache.settings import Settings as settings
from aiocache.cache import SimpleMemoryCache, RedisCache, MemcachedCache
from aiocache.decorators import cached, multi_cached


__all__ = (
    'settings',
    'cached',
    'caches',
    'multi_cached',
    'RedisCache',
    'SimpleMemoryCache',
    'MemcachedCache',
)


def _class_from_string(class_path):
    class_name = class_path.split('.')[-1]
    module_name = class_path.rstrip(class_name).rstrip(".")
    return getattr(__import__(module_name, fromlist=[class_name]), class_name)


def _create_cache(cache, serializer=None, plugins=None, **kwargs):

    if serializer is not None:
        cls = serializer.pop("class")
        cls = _class_from_string(cls) if isinstance(cls, str) else cls
        serializer = cls(**serializer)

    plugins_instances = []
    if plugins is not None:
        for plugin in plugins:
            cls = plugin.pop("class")
            cls = _class_from_string(cls) if isinstance(cls, str) else cls
            plugins_instances.append(cls(**plugin))

    cache = _class_from_string(cache) if isinstance(cache, str) else cache
    instance = cache(
        serializer=serializer,
        plugins=plugins_instances,
        **kwargs)
    return instance


class CacheHandler:

    def __init__(self):
        self._caches = {}

    def __getitem__(self, alias):
        try:
            return self._caches[alias]
        except KeyError:
            pass

        config = settings.get_config()
        if alias not in config:
            raise KeyError(
                "Could not find config for '{}' in settings, ensure you called settings.from_config"
                "specifying the config for that cache".format(alias))

        cache = _create_cache(**deepcopy(config[alias]))
        self._caches[alias] = cache
        return cache


caches = CacheHandler()
