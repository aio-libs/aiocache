from aiocache import settings, RedisCache
from aiocache.serializers import PickleSerializer
from aiocache.plugins import BasePlugin
from aiocache.utils import get_cache_value_with_fallbacks, get_cache


def test_get_cache_value_with_fallbacks_with_value():
    assert get_cache_value_with_fallbacks("value", "fake_key", "DEFAULT") == "value"


def test_get_cache_value_with_fallbacks_with_settings():
    settings.set_cache(RedisCache, fake_key="random")
    assert get_cache_value_with_fallbacks(None, "fake_key", "DEFAULT", cls=RedisCache) == "random"


def test_get_cache_value_with_fallbacks_with_default():
    assert get_cache_value_with_fallbacks(None, "fake_key", "DEFAULT") == "DEFAULT"


class TestCacheFactory:

    def test_get_cache(self):
        cache = get_cache(cache=RedisCache)

        assert isinstance(cache, RedisCache)

    def test_get_cache_with_default_config(self):
        settings.set_cache(
            "aiocache.RedisCache", endpoint="http://...", port=6379)
        cache = get_cache(
            namespace="default", serializer=PickleSerializer(),
            plugins=BasePlugin(), port=123)

        assert isinstance(cache, RedisCache)
        assert cache.endpoint == "http://..."
        assert cache.port == 123
        assert cache.namespace == "default"
        assert isinstance(cache.serializer, PickleSerializer)
        assert isinstance(cache.plugins, BasePlugin)

    def test_get_cache_with_default_plugins_kwargs(self):
        settings.set_cache(
            "aiocache.RedisCache", endpoint="http://...", port=6379)
        cache = get_cache(
            namespace="default", serializer=PickleSerializer(),
            plugins=BasePlugin(), port=123)

        assert isinstance(cache, RedisCache)
        assert cache.endpoint == "http://..."
        assert cache.port == 123
        assert cache.namespace == "default"
        assert isinstance(cache.serializer, PickleSerializer)
        assert isinstance(cache.plugins, BasePlugin)

    def test_get_cache_overrides(self):
        cache = get_cache(
            cache=RedisCache, namespace="default", serializer=PickleSerializer(),
            plugins=BasePlugin(), endpoint="http://...", port=123)

        assert isinstance(cache, RedisCache)
        assert cache.endpoint == "http://..."
        assert cache.port == 123
        assert cache.namespace == "default"
        assert isinstance(cache.serializer, PickleSerializer)
        assert isinstance(cache.plugins, BasePlugin)
