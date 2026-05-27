import pytest

from aiocache.backends.limited_memory import LimitedSizeMemoryCache

pytestmark = pytest.mark.asyncio


async def test_lru_eviction():
    cache = LimitedSizeMemoryCache(max_size_mb=1)
    v1 = "a" * 400_000
    v2 = "b" * 400_000
    v3 = "c" * 400_000

    await cache.set("k1", v1)
    await cache.set("k2", v2)

    # Touch k1 so k2 becomes LRU
    await cache.get("k1")

    await cache.set("k3", v3)

    assert await cache.get("k1") == v1
    assert await cache.get("k2") is None
    assert await cache.get("k3") == v3


async def test_oversize_item():
    big = "x" * (2 * 1024 * 1024)
    cache = LimitedSizeMemoryCache(max_size_mb=1)

    assert not await cache.set("big", big)
    assert not await cache.exists("big")

    cache = LimitedSizeMemoryCache(max_size_mb=1, raise_on_oversize=True)
    with pytest.raises(MemoryError):
        await cache.set("big", big)
