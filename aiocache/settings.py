import aiocache

from aiocache.utils import class_from_string
from aiocache.serializers import DefaultSerializer
from aiocache.policies import DefaultPolicy


DEFAULT_CACHE = aiocache.SimpleMemoryCache
DEFAULT_SERIALIZER = DefaultSerializer
DEFAULT_POLICY = DefaultPolicy
DEFAULT_NAMESPACE = None
DEFAULT_KWARGS = {}


def set_defaults(cache=None, namespace=None, serializer=None, policy=None, **kwargs):

    if cache:
        aiocache.settings.DEFAULT_CACHE = class_from_string(cache)
    if serializer:
        aiocache.settings.DEFAULT_SERIALIZER = class_from_string(serializer)
    if policy:
        aiocache.settings.DEFAULT_POLICY = class_from_string(policy)

    aiocache.settings.DEFAULT_NAMESPACE = namespace or ""
    aiocache.settings.DEFAULT_KWARGS = kwargs
