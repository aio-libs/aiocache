from .cache import SimpleMemoryCache, RedisCache, MemcachedCache
from .utils import cached, multi_cached


__all__ = (
    'cached',
    'multi_cached',
    'RedisCache',
    'SimpleMemoryCache',
    'MemcachedCache',
)


def config_default_cache(*args, **kwargs):
    default_cache = globals().get('default_cache')
    if not default_cache:
        cache = kwargs.pop('cache', SimpleMemoryCache)
        default_cache = globals()['default_cache'] = cache(*args, **kwargs)
        policy = kwargs.pop('policy', None)
        if policy:
            default_cache.set_policy(policy)
    return default_cache
