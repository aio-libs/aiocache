from .log import logger
from .settings import settings
from .backends.memory import SimpleMemoryCache
from .factory import caches
from .decorators import cached, multi_cached
from ._version import __version__


__cache_types = [SimpleMemoryCache]

try:
    import aioredis
except ImportError:
    logger.info("aioredis not installed, RedisCache unavailable")
else:
    from aiocache.backends.redis import RedisCache
    __cache_types.append(RedisCache)
    del aioredis

try:
    import aiomcache
except ImportError:
    logger.info("aiomcache not installed, Memcached unavailable")
else:
    from aiocache.backends.memcached import MemcachedCache
    __cache_types.append(MemcachedCache)
    del aiomcache


__all__ = (
    'caches',
    'settings',
    'cached',
    'multi_cached',
    *__cache_types,
    '__version__',
)
