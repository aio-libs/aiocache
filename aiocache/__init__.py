import logging
from typing import Any, List, Type

from .backends.memory import SimpleMemoryCache
from .base import BaseCache

__version__ = "1.0.0a0"

logger = logging.getLogger(__name__)

_AIOCACHE_CACHES: List[Type[BaseCache[Any]]] = [SimpleMemoryCache]

try:
    import redis
except ImportError:
    logger.debug("redis not installed, RedisCache unavailable")
else:
    from aiocache.backends.redis import RedisCache

    _AIOCACHE_CACHES.append(RedisCache)
    del redis

try:
    import aiomcache
except ImportError:
    logger.debug("aiomcache not installed, Memcached unavailable")
else:
    from aiocache.backends.memcached import MemcachedCache

    _AIOCACHE_CACHES.append(MemcachedCache)
    del aiomcache

from .decorators import cached, cached_stampede, multi_cached  # noqa: E402,I202

__all__ = (
    "cached",
    "cached_stampede",
    "multi_cached",
    *sorted(c.__name__ for c in _AIOCACHE_CACHES),
)
