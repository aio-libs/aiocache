from __future__ import annotations

import asyncio
import collections
import logging
import sys
from typing import Dict, Iterable, Optional

from aiocache.backends.memory import SimpleMemoryCache

__all__ = ("LimitedSizeMemoryCache",)

logger = logging.getLogger(__name__)


class LimitedSizeMemoryCache(SimpleMemoryCache):
    """In-memory cache with an LRU eviction policy and a global size limit.

    Parameters
    ----------
    max_size_mb: int
        Maximum cache size in megabytes. Defaults to ``64``.
    raise_on_oversize: bool
        If ``True``, trying to cache a single value bigger than ``max_size_mb``
        raises :class:`MemoryError`.  If ``False`` (default) the operation is
        silently skipped.
    """

    NAME = "limited_memory"

    def __init__(
        self,
        max_size_mb: int = 64,
        *,
        raise_on_oversize: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._max_bytes: int = max_size_mb * 1024 * 1024
        self._raise_oversize: bool = raise_on_oversize
        self._sizes: Dict[str, int] = {}
        self._lru: "collections.OrderedDict[str, None]" = collections.OrderedDict()
        self._current_bytes: int = 0

    def _estimate_size(self, value) -> int:
        """Return an approximate byte size of ``value`` after serialization."""
        blob = self._serializer.dumps(value)
        if isinstance(blob, (bytes, bytearray)):
            return len(blob)
        if isinstance(blob, str):
            return len(blob.encode())
        return sys.getsizeof(blob)

    def _touch(self, key: str) -> None:
        self._lru[key] = None
        self._lru.move_to_end(key)

    async def _evict_until_fits(self, extra_bytes: int) -> None:
        while self._lru and self._current_bytes + extra_bytes > self._max_bytes:
            victim, _ = self._lru.popitem(last=False)
            await super()._delete(victim)
            self._current_bytes -= self._sizes.pop(victim, 0)

    async def _get(self, key, encoding="utf-8", _conn=None):
        value = await super()._get(key, encoding=encoding, _conn=_conn)
        if value is not None:
            self._touch(key)
        return value

    async def _multi_get(self, keys: Iterable[str], encoding="utf-8", _conn=None):
        values = await super()._multi_get(keys, encoding=encoding, _conn=_conn)
        for k, v in zip(keys, values):
            if v is not None:
                self._touch(k)
        return values

    async def _set(self, key, value, ttl=None, _cas_token=None, _conn=None):
        new_size = self._estimate_size(value)
        old_size = self._sizes.get(key, 0)
        size_delta = new_size - old_size

        if new_size > self._max_bytes:
            if self._raise_oversize:
                raise MemoryError(
                    f"Item ({new_size / 1_048_576:.2f} MB) exceeds "
                    f"max_size_mb={self._max_bytes / 1_048_576:.2f}"
                )
            logger.debug(
                "Skipping insertion of %r (%.2f MB > %.2f MB)",
                key,
                new_size / 1_048_576,
                self._max_bytes / 1_048_576,
            )
            return False

        await self._evict_until_fits(size_delta)
        stored = await super()._set(
            key, value, ttl=None, _cas_token=_cas_token, _conn=_conn
        )
        if not stored:
            return stored

        self._current_bytes += size_delta
        self._sizes[key] = new_size
        self._touch(key)

        if key in self._handlers:
            self._handlers[key].cancel()
        if ttl:
            loop = asyncio.get_running_loop()
            self._handlers[key] = loop.call_later(ttl, self._expire_and_bookkeep, key)

        return stored

    async def _multi_set(self, pairs, ttl=None, _conn=None):
        for k, v in pairs:
            await self._set(k, v, ttl=ttl)
        return True

    async def _add(self, key, value, ttl=None, _conn=None):
        if await super()._exists(key):
            raise ValueError(f"Key {key!r} already exists, use .set to update")
        return await self._set(key, value, ttl=ttl)

    async def _delete(self, key, _conn=None):
        removed = await super()._delete(key)
        if removed:
            self._current_bytes -= self._sizes.pop(key, 0)
            self._lru.pop(key, None)
        return removed

    async def _clear(self, namespace: Optional[str] = None, _conn=None):
        await super()._clear(namespace, _conn=_conn)
        if namespace is None:
            self._sizes.clear()
            self._lru.clear()
            self._current_bytes = 0
            return True
        doomed = [k for k in self._sizes if k.startswith(namespace)]
        freed = sum(self._sizes.pop(k) for k in doomed)
        self._current_bytes -= freed
        for k in doomed:
            self._lru.pop(k, None)
        return True

    async def _expire(self, key, ttl, _conn=None):
        if key not in self._cache:
            return False
        handle = self._handlers.pop(key, None)
        if handle:
            handle.cancel()
        if ttl:
            loop = asyncio.get_running_loop()
            self._handlers[key] = loop.call_later(ttl, self._expire_and_bookkeep, key)
        return True

    def _expire_and_bookkeep(self, key: str) -> None:
        if self._cache.pop(key, None) is not None:
            handle = self._handlers.pop(key, None)
            if handle:
                handle.cancel()
            self._current_bytes -= self._sizes.pop(key, 0)
            self._lru.pop(key, None)
