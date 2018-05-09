import importlib
import warnings
from types import MappingProxyType
from typing import MutableMapping


def _class_from_string(class_path):
    class_name = class_path.split('.')[-1]
    module_name = class_path.rstrip(class_name).rstrip(".")
    return getattr(importlib.import_module(module_name), class_name)


def _create_cache(cache, serializer=None, plugins=None, **kwargs):
    if serializer is not None:
        cls = serializer['class']
        cls = _class_from_string(cls) if isinstance(cls, str) else cls
        serializer = cls(
            **{k: v for k, v in serializer.items() if k != 'class'}
        )

    plugins_instances = []
    if plugins is not None:
        for plugin in plugins:
            cls = plugin['class']
            cls = _class_from_string(cls) if isinstance(cls, str) else cls
            plugins_instances.append(
                cls(**{k: v for k, v in plugin.items() if k != 'class'})
            )

    cache = _class_from_string(cache) if isinstance(cache, str) else cache
    instance = cache(
        serializer=serializer,
        plugins=plugins_instances,
        **kwargs)
    return instance


class CacheHandler:
    """
    Cache handler.
    """
    _config = {
        'default': {
            'cache': 'aiocache.SimpleMemoryCache',
            'serializer': {
                'class': 'aiocache.serializers.StringSerializer'
            }
        }
    }

    def __init__(self):
        self._caches = {}

    def get(self, alias):
        """
        Retrieve cache identified by alias.
        Will return always the same instance.

        :param alias: str cache alias
        :return: cache instance
        """
        try:
            return self._caches[alias]
        except KeyError:
            pass

        config = self.get_alias_config(alias)
        cache = _create_cache(**config)
        self._caches[alias] = cache
        return cache

    def create(self, alias=None, cache=None, **kwargs):
        """
        Create a new cache. Either alias or cache params are required.
        You can use kwargs to pass extra parameters to configure the cache.

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

    def get_alias_config(self, alias) -> MappingProxyType:
        if alias not in self._config:
            raise KeyError(
                "Could not find config for '{0}', ensure you include {0} "
                "when calling caches.config setter specifying the config "
                "for that cache".format(alias)
            )

        return MappingProxyType(self.config[alias])

    @property
    def config(self) -> MappingProxyType:
        """
        Current stored config.

        :getter: Return mapping proxy to config
        :setter:
            Set (override) the default config for cache aliases
            from a dict-like structure. The structure is the following::

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

            'default' key must always exist when passing a new config.
            Default configuration is::

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

            If a config key already exists, it will be updated with the new values.
        :type: MappingProxyType
        """
        return MappingProxyType(self._config)

    def get_config(self):
        """
        Return a proxy to current stored config
        """
        warnings.warn(
            '"get_config" method is deprecated. Use "config" property instead.',
            DeprecationWarning
        )
        return self.config

    @config.setter
    def config(self, value: MutableMapping):
        if 'default' not in value:
            raise ValueError('default config must be provided')
        for config_name in value.keys():
            self._caches.pop(config_name, None)
        self._config = value

    def set_config(self, config: MutableMapping):
        """
        Set (override) the default config for cache aliases from a dict-like
        structure. The structure is the following::

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

        'default' key must always exist when passing a new config.
        Default configuration is::

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

        If a config key already exists, it will be updated with the new values.
        """
        warnings.warn(
            '"set_config" method is deprecated. '
            'Use "config" property setter instead.',
            DeprecationWarning
        )
        self.config = config


#: Initialized cache handler to use via direct importing
caches = CacheHandler()
