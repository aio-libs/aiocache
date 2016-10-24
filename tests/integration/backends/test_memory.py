import pytest


class TestMemoryCache:

    @pytest.mark.asyncio
    async def test_raw(self, memory_cache):
        await memory_cache.raw('setdefault', b"key", b"value")
        assert await memory_cache.raw("get", b"key") == b"value"
        assert list(await memory_cache.raw("keys")) == [b"key"]
