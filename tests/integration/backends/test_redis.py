from aiocache import RedisCache
from aiocache import serializers


class TestRedisCache:

    def test_setup(self, redis_cache):
        assert redis_cache.endpoint == "127.0.0.1"
        assert redis_cache.port == 6379

    def test_setup_override(self):
        redis_cache = RedisCache(serializer=serializers.JsonSerializer())
        assert redis_cache.endpoint == "127.0.0.1"
        assert redis_cache.port == 6379
        assert isinstance(redis_cache.serializer, serializers.JsonSerializer)
