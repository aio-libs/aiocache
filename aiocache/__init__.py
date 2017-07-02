from .log import logger
from .backends.memory import SimpleMemoryCache
from .factory import caches
from .decorators import cached, cached_stampede, multi_cached
from ._version import __version__


__cache_types = [SimpleMemoryCache.__name__]

try:
    import aioredis
except ImportError:
    logger.info("aioredis not installed, RedisCache unavailable")
else:
    from aiocache.backends.redis import RedisCache
    __cache_types.append(RedisCache.__name__)
    del aioredis

try:
    import aiomcache
except ImportError:
    logger.info("aiomcache not installed, Memcached unavailable")
else:
    from aiocache.backends.memcached import MemcachedCache
    __cache_types.append(MemcachedCache.__name__)
    del aiomcache


__all__ = (
    'caches',
    'cached',
    'cached_stampede',
    'multi_cached',
    *__cache_types,
    '__version__',
)
