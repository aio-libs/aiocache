import logging
from typing import Dict, Type

from ._version import __version__
from .backends.memory import SimpleMemoryCache
from .base import BaseCache

logger = logging.getLogger(__name__)

AIOCACHE_CACHES: Dict[str, Type[BaseCache]] = {SimpleMemoryCache.NAME: SimpleMemoryCache}

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

from .decorators import cached, cached_stampede, multi_cached  # noqa: E402,I202
from .factory import Cache, caches  # noqa: E402


__all__ = (
    "caches",
    "Cache",
    "cached",
    "cached_stampede",
    "multi_cached",
    *(c.__name__ for c in AIOCACHE_CACHES.values()),
    "__version__",
)
