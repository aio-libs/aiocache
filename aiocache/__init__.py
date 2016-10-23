from .backends import RedisCache, SimpleMemoryCache, MemcachedCache
from .utils import cached, multi_cached


__all__ = (
    'RedisCache',
    'SimpleMemoryCache',
    'MemcachedCache',
    'cached',
    'multi_cached',
)


def config_default_cache(*args, **kwargs):
    default_cache = globals().get('default_cache')
    if not default_cache:
        backend = kwargs.pop('backend', SimpleMemoryCache)
        default_cache = globals()['default_cache'] = backend(*args, **kwargs)
        policy = kwargs.pop('policy', None)
        if policy:
            default_cache.policy = policy
    return default_cache
