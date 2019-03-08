import logging

from .backends.memory import SimpleMemoryCache
from ._version import __version__


logger = logging.getLogger(__name__)

AIOCACHE_CACHES = {SimpleMemoryCache.NAME: SimpleMemoryCache}


try:
    import aioredis
except ImportError:
    logger.info("aioredis not installed, RedisCache unavailable")
else:
    from aiocache.backends.redis import RedisCache

    AIOCACHE_CACHES[RedisCache.NAME] = RedisCache
    del aioredis

try:
    import aiomcache
except ImportError:
    logger.info("aiomcache not installed, Memcached unavailable")
else:
    from aiocache.backends.memcached import MemcachedCache

    AIOCACHE_CACHES[MemcachedCache.NAME] = MemcachedCache
    del aiomcache


from .factory import caches, Cache  # noqa: E402
from .decorators import cached, cached_stampede, multi_cached  # noqa: E402


__all__ = (
    "caches",
    "Cache",
    "cached",
    "cached_stampede",
    "multi_cached",
    *list(AIOCACHE_CACHES.values()),
    "__version__",
)
