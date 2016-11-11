import aiocache

from aiocache.cache import SimpleMemoryCache, RedisCache, MemcachedCache
from aiocache.utils import cached, multi_cached, class_from_string
from aiocache.serializers import DefaultSerializer
from aiocache.policies import DefaultPolicy


__all__ = (
    'cached',
    'multi_cached',
    'RedisCache',
    'SimpleMemoryCache',
    'MemcachedCache',
)

DEFAULT_CACHE = SimpleMemoryCache
DEFAULT_SERIALIZER = DefaultSerializer
DEFAULT_POLICY = DefaultPolicy
DEFAULT_NAMESPACE = None
DEFAULT_KWARGS = {}


def set_defaults(cache=None, namespace=None, serializer=None, policy=None, **kwargs):
    aiocache.DEFAULT_CACHE = class_from_string(cache) if cache else SimpleMemoryCache
    aiocache.DEFAULT_NAMESPACE = namespace or ""
    aiocache.DEFAULT_KWARGS = kwargs
    aiocache.DEFAULT_SERIALIZER = class_from_string(serializer) if serializer else DefaultSerializer
    aiocache.DEFAULT_POLICY = class_from_string(policy) if policy else DefaultPolicy
