from .backends import RedisCache, SimpleMemoryCache, MemcachedCache
from .utils import cached, multi_cached


__all__ = (
    'RedisCache',
    'SimpleMemoryCache',
    'MemcachedCache',
    'cached',
    'multi_cached',
)


default_cache = None


def config_default_cache(*args, **kwargs):
    global default_cache
    backend = kwargs.pop('backend', SimpleMemoryCache)
    default_cache = backend(*args, **kwargs)
    policy = kwargs.pop('policy', None)
    if policy:
        default_cache.policy = policy
    return default_cache
