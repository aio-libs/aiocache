import pytest

from aiocache import (
    _class_from_string, _create_cache,
    SimpleMemoryCache, RedisCache, settings, caches)
from aiocache.serializers import PickleSerializer
from aiocache.plugins import TimingPlugin


def test_class_from_string():
    assert _class_from_string("aiocache.RedisCache") == RedisCache


def test_create_simple_cache():
    redis = _create_cache(RedisCache, endpoint="127.0.0.10", port=6378)

    assert isinstance(redis, RedisCache)
    assert redis.endpoint == "127.0.0.10"
    assert redis.port == 6378


def test_create_cache_with_everything():
    redis = _create_cache(
            RedisCache,
            serializer={'class': PickleSerializer},
            plugins=[{'class': "aiocache.plugins.TimingPlugin"}])

    assert isinstance(redis.serializer, PickleSerializer)
    assert isinstance(redis.plugins[0], TimingPlugin)


class TestCacheHandler:

    @pytest.fixture(autouse=True)
    def remove_caches(self):
        caches._caches = {}

    def test_get_wrong_alias(self):
        with pytest.raises(KeyError):
            caches["wrong_cache"]

        with pytest.raises(KeyError):
            caches.create("wrong_cache")

    def test_reuse_instance(self):
        assert caches['default'] is caches['default']

    def test_create_not_reuse(self):
        assert caches.create('default') is not caches.create('default')

    def test_retrieve_cache(self):
        settings.set_config({
            'default': {
                'cache': "aiocache.RedisCache",
                'endpoint': "127.0.0.10",
                'port': 6378,
                'serializer': {
                    'class': "aiocache.serializers.PickleSerializer"
                },
                'plugins': [
                    {'class': "aiocache.plugins.HitMissRatioPlugin"},
                    {'class': "aiocache.plugins.TimingPlugin"}
                ]
            }
        })

        cache = caches['default']
        assert isinstance(cache, RedisCache)
        assert cache.endpoint == "127.0.0.10"
        assert cache.port == 6378
        assert isinstance(cache.serializer, PickleSerializer)
        assert len(cache.plugins) == 2

    def test_retrieve_cache_new_instance(self):
        settings.set_config({
            'default': {
                'cache': "aiocache.RedisCache",
                'endpoint': "127.0.0.10",
                'port': 6378,
                'serializer': {
                    'class': "aiocache.serializers.PickleSerializer"
                },
                'plugins': [
                    {'class': "aiocache.plugins.HitMissRatioPlugin"},
                    {'class': "aiocache.plugins.TimingPlugin"}
                ]
            }
        })

        cache = caches.create('default')
        assert isinstance(cache, RedisCache)
        assert cache.endpoint == "127.0.0.10"
        assert cache.port == 6378
        assert isinstance(cache.serializer, PickleSerializer)
        assert len(cache.plugins) == 2

    def test_multiple_caches(self):
        settings.set_config({
            'default': {
                'cache': "aiocache.RedisCache",
                'endpoint': "127.0.0.10",
                'port': 6378,
                'serializer': {
                    'class': "aiocache.serializers.PickleSerializer"
                },
                'plugins': [
                    {'class': "aiocache.plugins.HitMissRatioPlugin"},
                    {'class': "aiocache.plugins.TimingPlugin"}
                ]
            },
            'alt': {
                'cache': "aiocache.SimpleMemoryCache",
            }
        })

        default = caches['default']
        alt = caches['alt']

        assert isinstance(default, RedisCache)
        assert default.endpoint == "127.0.0.10"
        assert default.port == 6378
        assert isinstance(default.serializer, PickleSerializer)
        assert len(default.plugins) == 2

        assert isinstance(alt, SimpleMemoryCache)
