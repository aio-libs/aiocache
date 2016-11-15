from aiocache import SimpleMemoryCache
from aiocache.utils import class_from_string
from aiocache.serializers import DefaultSerializer
from aiocache.policies import DefaultPolicy


DEFAULT_CACHE = SimpleMemoryCache
DEFAULT_CACHE_KWARGS = {}

DEFAULT_SERIALIZER = DefaultSerializer
DEFAULT_SERIALIZER_KWARGS = {}

DEFAULT_POLICY = DefaultPolicy
DEFAULT_POLICY_KWARGS = {}


def set_defaults(class_=None, **kwargs):
    """
    Set the default settings for the cache. If within your project you are working with a Redis
    backend, you can use it as::

        aiocache.settings.set_defaults(
            class_="aiocache.RedisCache", endpoint="127.0.0.1", port=6379, namespace="test")

    Once the call is done, all decorators and instances where thos params are not specified, the
    default ones will be picked.
    """
    if class_:
        globals()['DEFAULT_CACHE'] = class_from_string(class_)
    globals()['DEFAULT_CACHE_KWARGS'] = kwargs


def set_default_serializer(class_=None, **kwargs):
    """
    Set the default settings for the serializer. If within your project you are working with
    json objects, you may want to call it as::

        aiocache.settings.set_default_serializer(
            class_="aiocache.serializers.DefaultSerializer")

    Once the call is done, all decorators and instances where serializer params are not specified,
    the default ones will be picked.

    If you define your own serializer, you can also set is a default and pass the desired extra
    params through this call.
    """
    if class_:
        globals()['DEFAULT_SERIALIZER'] = class_from_string(class_)
    globals()['DEFAULT_SERIALIZER_KWARGS'] = kwargs


def set_default_policy(class_=None, **kwargs):
    """
    Set the default settings for the policy. If within your project you are working with a
    custom policy, you may want to call it as::

        aiocache.settings.set_default_policy(
            class_="my_module.MyPolicy")

    Once the call is done, all decorators and instances where policiy params are not specified,
    the default ones will be picked.

    If you define your own policy, you can also set is a default and pass the desired extra
    params through this call.
    """
    if class_:
        globals()['DEFAULT_POLICY'] = class_from_string(class_)
    globals()['DEFAULT_POLICY_KWARGS'] = kwargs


def get_defaults():
    return {
        "DEFAULT_CACHE": DEFAULT_CACHE,
        "DEFAULT_CACHE_KWARGS": DEFAULT_CACHE_KWARGS,
        "DEFAULT_SERIALIZER": DEFAULT_SERIALIZER,
        "DEFAULT_SERIALIZER_KWARGS": DEFAULT_SERIALIZER_KWARGS,
        "DEFAULT_POLICY": DEFAULT_POLICY,
        "DEFAULT_POLICY_KWARGS": DEFAULT_POLICY_KWARGS,
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
            "POLICY": {
                "class": "aiocache.policies.DefaultPolicy"
            }
        }

    Of course you can set your own classes there. Any extra parameter you put in the dict will be
    used for new instantiations if those are not set explicitly when calling it.

    All keys in the config are optional, if they are not passed the previous defaults will be kept.
    """

    if "CACHE" in config:
        class_ = config['CACHE'].pop("class", None)
        set_defaults(class_=class_, **config['CACHE'])

    if "SERIALIZER" in config:
        class_ = config['SERIALIZER'].pop("class", None)
        set_default_serializer(class_=class_, **config['SERIALIZER'])

    if "POLICY" in config:
        class_ = config['POLICY'].pop("class", None)
        set_default_policy(class_=class_, **config['POLICY'])
