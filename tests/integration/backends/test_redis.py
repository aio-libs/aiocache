import pytest

from aiocache import RedisCache
from aiocache import serializers


class TestRedisBackend:

    @pytest.mark.asyncio
    async def test_setup(self, redis_cache):
        assert redis_cache._backend.endpoint == "127.0.0.1"
        assert redis_cache._backend.port == 6379

    @pytest.mark.asyncio
    async def test_setup_override(self):
        redis_cache = RedisCache(serializer=serializers.JsonSerializer())
        assert redis_cache._backend.endpoint == "127.0.0.1"
        assert redis_cache._backend.port == 6379
        assert isinstance(redis_cache.serializer, serializers.JsonSerializer)

    @pytest.mark.asyncio
    async def test_raw(self, redis_cache):
        await redis_cache.raw('set', b"key", b"value")
        assert await redis_cache.raw("get", b"key") == b"value"
        assert await redis_cache.raw("keys", "k*") == [b"key"]
