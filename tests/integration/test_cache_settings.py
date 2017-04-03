import pytest
import aiocache

from aiocache import RedisCache


@pytest.fixture(autouse=True)
def reset_defaults():
    aiocache.settings.set_from_dict({
        "CACHE": {
            "class": "aiocache.SimpleMemoryCache",
        },
        "SERIALIZER": {
            "class": "aiocache.serializers.DefaultSerializer",
        },
        "PLUGINS": []
    })


class TestRedisSettings:
    def test_cache_settings(self):
        aiocache.settings.set_defaults(
            class_=aiocache.RedisCache, endpoint="127.0.0.1", port=6379, timeout=10, db=1)
        cache = RedisCache(db=0)

        assert cache.endpoint == "127.0.0.1"
        assert cache.port == 6379
        assert cache.timeout == 10
        assert cache.db == 0
