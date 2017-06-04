from copy import deepcopy


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

    _config = {
        'default': {
            'cache': "aiocache.SimpleMemoryCache",
            'serializer': {
                'class': "aiocache.serializers.StringSerializer"
            }
        }
    }

    def __init__(self):
        self._caches = {}

    def get(self, alias):
        """
        Retrieve cache identified by alias. Will return always the same instance

        :param alias: str cache alias
        :return: cache instance
        """
        try:
            return self._caches[alias]
        except KeyError:
            pass

        config = self.get_alias_config(alias)
        cache = _create_cache(**deepcopy(config))
        self._caches[alias] = cache
        return cache

    def create(self, alias=None, cache=None, **kwargs):
        """
        Create a new cache. Either alias or cache params are required. You can use
        kwargs to pass extra parameters to configure the cache.

        :param alias: str alias to pull configuration from
        :param cache: str or class cache class to use for creating the
            new cache (when no alias is used)
        :return: New cache instance
        """
        if alias:
            config = self.get_alias_config(alias)
        elif cache:
            config = {'cache': cache}
        else:
            raise TypeError("create call needs to receive an alias or a cache")
        cache = _create_cache(**{**config, **kwargs})
        return cache

    def get_alias_config(self, alias):
        config = self.get_config()
        if alias not in config:
            raise KeyError(
                "Could not find config for '{0}', ensure you include {0} when calling"
                "caches.set_config specifying the config for that cache".format(alias))

        return config[alias]

    def get_config(self):
        """
        Return copy of current stored config
        """
        return deepcopy(self._config)

    def set_config(self, config):
        """
        Set (override) the default config for cache aliases from a dict-like structure.
        The structure is the following::

            {
                'default': {
                    'cache': "aiocache.SimpleMemoryCache",
                    'serializer': {
                        'class': "aiocache.serializers.StringSerializer"
                    }
                },
                'redis_alt': {
                    'cache': "aiocache.RedisCache",
                    'endpoint': "127.0.0.10",
                    'port': 6378,
                    'serializer': {
                        'class': "aiocache.serializers.PickleSerializer"
                    },
                    'plugins': [
                        {'class': "aiocache.plugins.HitMissRatioPlugin"},
                        {'class': "aiocache.plugins.TimingPlugin"}
                    ]
                }
            }

        'default' key must always exist when passing a new config. Default configuration
        is::

            {
                'default': {
                    'cache': "aiocache.SimpleMemoryCache",
                    'serializer': {
                        'class': "aiocache.serializers.StringSerializer"
                    }
                }
            }

        You can set your own classes there.
        The class params accept both str and class types.

        All keys in the config are optional, if they are not passed the defaults
        for the specified class will be used.
        """
        if "default" not in config:
            raise ValueError("default config must be provided")
        self._config = config


caches = CacheHandler()
