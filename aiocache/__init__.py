import aiocache

from aiocache.cache import SimpleMemoryCache, RedisCache, MemcachedCache
from aiocache.utils import cached, multi_cached
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
    aiocache.DEFAULT_CACHE = cache or SimpleMemoryCache
    aiocache.DEFAULT_NAMESPACE = namespace or ""
    aiocache.DEFAULT_KWARGS = kwargs
    aiocache.DEFAULT_SERIALIZER = serializer or DefaultSerializer
    aiocache.DEFAULT_POLICY = policy or DefaultPolicy
