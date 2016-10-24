import pytest


class TestMemcachedCache:

    @pytest.mark.asyncio
    async def test_raw(self, memcached_cache):
        await memcached_cache.raw('set', b"key", b"value")
        assert await memcached_cache.raw("get", b"key") == b"value"
        assert await memcached_cache.raw("prepend", b"key", b"super") is True
        assert await memcached_cache.raw("get", b"key") == b"supervalue"
