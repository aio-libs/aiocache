import inspect

from aiocache import SimpleMemoryCache
from aiocache.log import logger
from aiocache.cache import BaseCache
from aiocache.utils import class_from_string
from aiocache.serializers import DefaultSerializer
from aiocache.plugins import BasePlugin


DEFAULT_CACHE = SimpleMemoryCache
DEFAULT_CACHE_KWARGS = {}

DEFAULT_SERIALIZER = DefaultSerializer
DEFAULT_SERIALIZER_KWARGS = {}

DEFAULT_PLUGINS = {}


def set_defaults(class_=SimpleMemoryCache, **kwargs):
    """
    Set the default settings for the cache. If within your project you are working with a Redis
    backend, you can use it as::

        aiocache.settings.set_defaults(
            class_="aiocache.RedisCache", endpoint="127.0.0.1", port=6379, namespace="test")

    Once the call is done, all decorators and instances where those params are not specified, the
    default ones will be picked. The class_ param accepts both str and class types.
    """
    if class_:
        if isinstance(class_, str) and issubclass(class_from_string(class_), BaseCache):
            globals()['DEFAULT_CACHE'] = class_from_string(class_)
        elif inspect.isclass(class_) and issubclass(class_, BaseCache):
            globals()['DEFAULT_CACHE'] = class_
        else:
            raise ValueError(
                "DEFAULT_CACHE must be a str or class subclassing aiocache.cache.BaseCache")
    globals()['DEFAULT_CACHE_KWARGS'] = kwargs


def set_default_serializer(class_=DefaultSerializer, **kwargs):
    """
    Set the default settings for the serializer. If within your project you are working with
    json objects, you may want to call it as::

        aiocache.settings.set_default_serializer(
            class_="aiocache.serializers.DefaultSerializer")

    Once the call is done, all decorators and instances where serializer params are not specified,
    the default ones will be picked. The class_ param accepts both str and class types.

    If you define your own serializer, you can also set is a default and pass the desired extra
    params through this call.
    """
    if class_:
        if isinstance(class_, str) and issubclass(class_from_string(class_), DefaultSerializer):
            globals()['DEFAULT_SERIALIZER'] = class_from_string(class_)
        elif inspect.isclass(class_) and issubclass(class_, DefaultSerializer):
            globals()['DEFAULT_SERIALIZER'] = class_
        else:
            raise ValueError(
                "DEFAULT_SERIALIZER must be a str or class \
                subclassing aiocache.serializers.DefaultSerializer")
    globals()['DEFAULT_SERIALIZER_KWARGS'] = kwargs


def set_default_plugins(config):
    """
    Set the default settings for the plugins. If within your project you are working with a
    custom plugin, you may want to call it as::

        aiocache.settings.set_default_plugins([
            {
                'class': MyPlugin,
            },
            {
                'class': 'my_module.OtherPlugin',
                'arg': 1
            }
        })

    Once the call is done, all decorators and instances where plugin params are not specified,
    the default ones will be picked. The class_ param accepts both str and class types.

    If you define your own plugin, you can also set is a default and pass the desired extra
    params through this call.
    """
    new_plugins = {}
    for plugin in config:
        class_ = plugin.pop('class')
        if isinstance(class_, str) and issubclass(class_from_string(class_), BasePlugin):
            new_plugins[class_from_string(class_)] = plugin
        elif inspect.isclass(class_) and issubclass(class_, BasePlugin):
            new_plugins[class_] = plugin
        else:
            logger.warning(
                "%s must be a str or class subclassing aiocache.plugins.BasePlugin" % class_)

    globals()['DEFAULT_PLUGINS'] = new_plugins


def get_defaults():
    return {
        "DEFAULT_CACHE": DEFAULT_CACHE,
        "DEFAULT_CACHE_KWARGS": DEFAULT_CACHE_KWARGS,
        "DEFAULT_SERIALIZER": DEFAULT_SERIALIZER,
        "DEFAULT_SERIALIZER_KWARGS": DEFAULT_SERIALIZER_KWARGS,
        "DEFAULT_PLUGINS": DEFAULT_PLUGINS,
    }


def set_from_dict(config):
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

    Of course you can set your own classes there. Any extra parameter you put in the dict will be
    used for new instantiations if those are not set explicitly when calling it. The class param
    accepts both str and class types.

    All keys in the config are optional, if they are not passed the previous defaults will be kept.
    """
    if "CACHE" in config:
        class_ = config['CACHE'].pop("class", None)
        set_defaults(class_=class_, **config['CACHE'])

    if "SERIALIZER" in config:
        class_ = config['SERIALIZER'].pop("class", None)
        set_default_serializer(class_=class_, **config['SERIALIZER'])

    if "PLUGINS" in config:
        set_default_plugins(config=config['PLUGINS'])
