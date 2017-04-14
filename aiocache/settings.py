"""
This module is depended by many other modules for pulling the default settings. In order to avoid
circular imports, this module must not depend on any other module from aiocache.
"""
import inspect


def class_from_string(class_path):
    class_name = class_path.split('.')[-1]
    module_name = class_path.rstrip(class_name).rstrip(".")
    return getattr(__import__(module_name, fromlist=[class_name]), class_name)


class Settings:

    __instance = None
    _CACHE = "aiocache.SimpleMemoryCache"
    _CACHE_KWARGS = {}

    _SERIALIZER = "aiocache.serializers.DefaultSerializer"
    _SERIALIZER_KWARGS = {}

    _PLUGINS = {}

    def __new__(cls):

        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    @classmethod
    def get_cache_class(cls):
        """
        Get the default class configured
        :returns: class set as default cache
        """
        if isinstance(cls._CACHE, str):
            return class_from_string(cls._CACHE)
        return cls._CACHE

    @classmethod
    def get_cache_args(cls):
        """
        Get the **kwargs configured for the default cache
        :returns: dict containing the default args
        """
        return cls._CACHE_KWARGS

    @classmethod
    def get_serializer_class(cls):
        """
        Get the default serializer configured
        :returns: class set as default serializer
        """
        if isinstance(cls._SERIALIZER, str):
            return class_from_string(cls._SERIALIZER)
        return cls._SERIALIZER

    @classmethod
    def get_serializer_args(cls):
        """
        Get the **kwargs configured for the default serializer
        :returns: dict containing the default args
        """
        return cls._SERIALIZER_KWARGS

    @classmethod
    def get_plugins_class(cls):
        """
        Get the default plugins classes configured
        :returns: iterable of classes
        """
        return cls._PLUGINS.keys()

    @classmethod
    def get_plugins_args(cls):
        """
        Get the **kwargs configured for each plugin. Order matches with
        the list returned by ``get_plugins_class``.
        """
        return cls._PLUGINS.values()

    @classmethod
    def get_defaults(cls):
        return {
            "CACHE": cls.get_cache_class(),
            "CACHE_KWARGS": cls.get_cache_args(),
            "SERIALIZER": cls.get_serializer_class(),
            "SERIALIZER_KWARGS": cls.get_serializer_args(),
            "PLUGINS": cls._PLUGINS,
        }

    @classmethod
    def set_cache(cls, cache, **kwargs):
        """
        Set default cache and its config. If within your project you are working with a Redis
        backend, you can use it as::

            aiocache.settings.set_cache(
                "aiocache.RedisCache", endpoint="127.0.0.1", port=6379, namespace="test")

        Once the call is done, all decorators and instances where those params are not specified,
        the default ones will be picked. The cache param accepts both str and class types.

        The kwargs are overridden in every call. If you pass empty kwargs, defaults will be cleared
        despite that there were values before.
        """
        if isinstance(cache, str) and issubclass(
                class_from_string(cache), class_from_string("aiocache.cache.BaseCache")):
            cls._CACHE = class_from_string(cache)
        elif inspect.isclass(cache) and issubclass(
                cache, class_from_string("aiocache.cache.BaseCache")):
            cls._CACHE = cache
        else:
            raise ValueError(
                "Cache '%s' must be a str or class subclassing aiocache.cache.BaseCache" % cache)
        cls._CACHE_KWARGS = kwargs

    @classmethod
    def set_serializer(cls, serializer, **kwargs):
        """
        Set default serializer and its config. If within your project you are working with
        json objects, you may want to call it as::

            aiocache.settings.set_serializer(
                "aiocache.serializers.JsonSerializer")

        Once the call is done, all decorators and instances where serializer params are
        not specified, the default ones will be picked. The serializer param accepts both str
        and class types.

        If you define your own serializer, you can also set it as default and pass the desired extra
        params through this call.

        The kwargs are overridden in every call. If you pass empty kwargs, defaults will be cleared
        despite that there were values before.
        """
        if isinstance(serializer, str) and issubclass(
                class_from_string(
                    serializer), class_from_string("aiocache.serializers.DefaultSerializer")):
            cls._SERIALIZER = class_from_string(serializer)
        elif inspect.isclass(serializer) and issubclass(
                serializer, class_from_string("aiocache.serializers.DefaultSerializer")):
            cls._SERIALIZER = serializer
        else:
            raise ValueError(
                "Serializer '%s' must be a str or class \
                subclassing aiocache.serializers.DefaultSerializer" % serializer)
        cls._SERIALIZER_KWARGS = kwargs

    @classmethod
    def set_plugins(cls, config):
        """
        Set the default plugins and their config. If within your project you are working with a
        custom plugin, you may want to call it as::

            settings.set_plugins([
                {
                    'class': MyPlugin,
                },
                {
                    'class': 'my_module.OtherPlugin',
                    'arg': 1
                }
            })

        Once the call is done, all decorators and instances where plugin params are not specified,
        the default ones will be picked. The class param accepts both str and class types.

        If you define your own plugin, you can also set is a default and pass the desired extra
        params through this call.

        The kwargs are overridden in every call. If you pass empty kwargs, defaults will be cleared
        despite that there were values before.
        """
        new_plugins = {}
        for plugin in config:
            class_ = plugin.pop('class')
            if isinstance(class_, str) and issubclass(
                    class_from_string(class_), class_from_string("aiocache.plugins.BasePlugin")):
                new_plugins[class_from_string(class_)] = plugin
            elif inspect.isclass(class_) and issubclass(
                    class_, class_from_string("aiocache.plugins.BasePlugin")):
                new_plugins[class_] = plugin
            else:
                raise ValueError(
                    "Plugin '%s' must be a str or class"
                    "subclassing aiocache.plugins.BasePlugin" % class_)

        cls._PLUGINS = new_plugins

    @classmethod
    def set_config(cls, config):
        """
        Set the default settings for aiocache from a dict-like structure. The structure is the
        following::

            {
                "CACHE": {
                    "class": "aiocache.RedisCache",
                    "endpoint": "127.0.0.1",
                    "port": 6379
                },
                "SERIALIZER": {
                    "class": "aiocache.serializers.DefaultSerializer"
                },
                "PLUGINS": [
                    {
                        "class": "aiocache.plugins.BasePlugin"
                    }
                ]
            }

        Of course you can set your own classes there. Any extra parameter you put in the
        dict will be used for new instantiations if those are not set explicitly when calling it.
        The class param accepts both str and class types.

        All keys in the config are optional, if they are not passed the previous defaults will
        be kept.
        """
        if "CACHE" in config:
            class_ = config['CACHE'].pop("class", None)
            cls.set_cache(class_, **config['CACHE'])

        if "SERIALIZER" in config:
            class_ = config['SERIALIZER'].pop("class", None)
            cls.set_serializer(class_, **config['SERIALIZER'])

        if "PLUGINS" in config:
            cls.set_plugins(config=config['PLUGINS'])
