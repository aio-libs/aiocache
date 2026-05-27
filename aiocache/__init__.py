import logging
from typing import Any, Type

from .backends.memory import SimpleMemoryCache
from .backends.limited_memory import LimitedSizeMemoryCache
from .base import BaseCache

__version__ = "1.0.0a0"

logger = logging.getLogger(__name__)

_AIOCACHE_CACHES: list[Type[BaseCache[Any]]] = [
    SimpleMemoryCache,
    LimitedSizeMemoryCache,
]

try:
    import glide
except ImportError:
    logger.debug("glide not installed, ValkeyCache unavailable")
else:
    from aiocache.backends.valkey import ValkeyCache

    _AIOCACHE_CACHES.append(ValkeyCache)
    del glide

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
