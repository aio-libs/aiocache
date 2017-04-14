import pytest
import aiocache

from aiocache import SimpleMemoryCache, settings
from aiocache.serializers import DefaultSerializer
from aiocache.plugins import BasePlugin


class TestSettings:

    def test_settings_singleton(self):
        assert settings() is settings()

    def test_default_settings(self):
        assert settings._CACHE == SimpleMemoryCache
        assert settings._CACHE_KWARGS == {}

        assert settings._SERIALIZER == DefaultSerializer
        assert settings._SERIALIZER_KWARGS == {}

        assert settings._PLUGINS == {}

    def test_get_cache_class(self):
        assert settings.get_cache_class() == SimpleMemoryCache

    def test_get_cache_class_when_str(self):
        settings._CACHE = "aiocache.SimpleMemoryCache"
        assert settings.get_cache_class() == SimpleMemoryCache

    def test_get_cache_args(self):
        assert settings.get_cache_args() == {}

    def test_get_serializer(self):
        assert settings.get_serializer_class() == DefaultSerializer

    def test_get_serializer_when_str(self):
        settings._SERIALIZER = "aiocache.serializers.DefaultSerializer"
        assert settings.get_serializer_class() == DefaultSerializer

    def test_get_serializer_args(self):
        assert settings.get_serializer_args() == {}

    def test_get_plugins(self):
        assert list(settings.get_plugins_class()) == []

    def test_get_plugins_args(self):
        assert list(settings.get_plugins_args()) == []

    def test_set_cache_without_arg(self):
        with pytest.raises(TypeError):
            settings.set_cache(
                endpoint="127.0.0.1", port=6379)

    def test_set_cache_no_kwargs(self):
        settings.set_cache(
            "aiocache.RedisCache", endpoint="127.0.0.1", port=6379)
        settings.set_cache(
            "aiocache.RedisCache")

        assert settings._CACHE_KWARGS == {}

    def test_set_cache_str(self):
        settings.set_cache(
            "aiocache.RedisCache", endpoint="127.0.0.1", port=6379)

        assert settings._CACHE == aiocache.RedisCache
        assert settings._CACHE_KWARGS == {"endpoint": "127.0.0.1", "port": 6379}

    def test_set_cache_str_fail(self):
        with pytest.raises(ValueError):
            settings.set_cache(
                "aiocache.serializers.DefaultSerializer", endpoint="127.0.0.1", port=6379)

    def test_set_cache_class(self):
        settings.set_cache(
            aiocache.RedisCache, endpoint="127.0.0.1", port=6379)

        assert settings._CACHE == aiocache.RedisCache
        assert settings._CACHE_KWARGS == {"endpoint": "127.0.0.1", "port": 6379}

    def test_set_cache_class_fail(self):
        with pytest.raises(ValueError):
            settings.set_cache(
                DefaultSerializer, endpoint="127.0.0.1", port=6379)

    def test_set_serializer_without_arg(self):
        with pytest.raises(TypeError):
            settings.set_serializer()

    def test_set_serializer_no_kwargs(self):
        settings.set_serializer(
            "aiocache.serializers.DefaultSerializer", endpoint="127.0.0.1", port=6379)
        settings.set_serializer(
            "aiocache.serializers.DefaultSerializer")

        assert settings._SERIALIZER_KWARGS == {}

    def test_set_serializer_str(self):
        settings.set_serializer(
            "aiocache.serializers.DefaultSerializer", random_attr="random_value")

        assert settings._SERIALIZER == DefaultSerializer
        assert settings._SERIALIZER_KWARGS == {"random_attr": "random_value"}

    def test_set_serializer_str_fail(self):
        with pytest.raises(ValueError):
            settings.set_serializer(
                "aiocache.RedisCache", random_attr="random_value")

    def test_set_serializer_class(self):
        settings.set_serializer(
            DefaultSerializer, random_attr="random_value")

        assert settings._SERIALIZER == DefaultSerializer
        assert settings._SERIALIZER_KWARGS == {"random_attr": "random_value"}

    def test_set_serializer_class_fail(self):
        with pytest.raises(ValueError):
            settings.set_serializer(
                aiocache.RedisCache, random_attr="random_value")

    def test_set_plugins_str(self):
        settings.set_plugins(
            [{"class": "aiocache.plugins.BasePlugin", "max_keys": 2}])

        assert settings._PLUGINS == {
            BasePlugin: {"max_keys": 2}}

    def test_set_plugin_no_kwargs(self):
        settings.set_plugins(
            [{"class": "aiocache.plugins.BasePlugin", "max_keys": 2}])
        settings.set_plugins(
            [{"class": "aiocache.plugins.BasePlugin"}])

        assert settings._PLUGINS == {BasePlugin: {}}

    def test_set_plugins_str_fail(self):
        with pytest.raises(ValueError):
            settings.set_plugins(
                [{"class": "aiocache.RedisCache", "random_attr": "random_value"}])

    def test_set_plugins_class(self):
        settings.set_plugins(
            [{"class": BasePlugin, "random_attr": "random_value"}])

        assert settings._PLUGINS == {
            BasePlugin: {"random_attr": "random_value"}}

    def test_set_plugins_class_fail(self):
        with pytest.raises(ValueError):
            settings.set_plugins(
                [{"class": aiocache.RedisCache, "random_attr": "random_value"}])

    def test_set_empty_config(self):
        old_settings = settings.get_defaults()
        settings.set_config({})
        assert settings.get_defaults() == old_settings

    def test_set_config_reset_kwargs(self):
        settings.set_config({
            "CACHE": {
                "class": "aiocache.RedisCache",
                "endpoint": "123123"}})
        settings.set_config({
            "CACHE": {
                "class": "aiocache.RedisCache"}})
        assert settings.get_cache_args() == {}

    def test_set_config(self):
        config = {
            "CACHE": {
                "class": aiocache.RedisCache,
                "endpoint": "127.0.0.1",
                "port": 6379
            },
            "SERIALIZER": {
                "class": "aiocache.serializers.DefaultSerializer",
                "random_attr": "random_value"
            },
            "PLUGINS": [
                {
                    "class": BasePlugin,
                    "max_keys": 2
                }
            ]
        }

        settings.set_config(config)

        assert settings._CACHE == aiocache.RedisCache
        assert settings._CACHE_KWARGS == {"endpoint": "127.0.0.1", "port": 6379}

        assert settings._SERIALIZER == DefaultSerializer
        assert settings._SERIALIZER_KWARGS == {"random_attr": "random_value"}

        assert settings._PLUGINS == {BasePlugin: {"max_keys": 2}}

    def test_get_defaults(self):
        assert settings.get_defaults() == {
            "CACHE": aiocache.SimpleMemoryCache,
            "CACHE_KWARGS": {},
            "SERIALIZER": DefaultSerializer,
            "SERIALIZER_KWARGS": {},
            "PLUGINS": {}
        }
