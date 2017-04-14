from aiocache.settings import Settings as settings
from aiocache.decorators import cached, multi_cached
from aiocache.cache import SimpleMemoryCache, RedisCache, MemcachedCache


__all__ = (
    'settings',
    'cached',
    'multi_cached',
    'RedisCache',
    'SimpleMemoryCache',
    'MemcachedCache',
)
