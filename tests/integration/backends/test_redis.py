import pytest

from aiocache import RedisCache
from aiocache import serializers


class TestRedisBackend:

    def test_setup(self):
        redis_cache = RedisCache()
        assert redis_cache.endpoint == "127.0.0.1"
        assert redis_cache.port == 6379
        assert redis_cache.encoding == "utf-8"

    def test_setup_override(self):
        redis_cache = RedisCache(
            serializer=serializers.JsonSerializer(),
            db=2,
            password="pass")

        assert redis_cache.endpoint == "127.0.0.1"
        assert redis_cache.port == 6379
        assert redis_cache.database == 2
        assert redis_cache.password == "pass"
        assert isinstance(redis_cache.serializer, serializers.JsonSerializer)

    @pytest.mark.asyncio
    async def test_raw(self, redis_cache):
        await redis_cache.raw('set', "key", "value")
        assert await redis_cache.raw("get", "key") == "value"
        assert await redis_cache.raw("keys", "k*") == ["key"]
