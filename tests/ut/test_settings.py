import pytest
import aiocache

from aiocache import SimpleMemoryCache
from aiocache.serializers import DefaultSerializer
from aiocache.policies import DefaultPolicy


class TestSettings:

    def test_default_settings(self):

        assert aiocache.settings.DEFAULT_CACHE == SimpleMemoryCache
        assert aiocache.settings.DEFAULT_CACHE_KWARGS == {}

        assert aiocache.settings.DEFAULT_SERIALIZER == DefaultSerializer
        assert aiocache.settings.DEFAULT_SERIALIZER_KWARGS == {}

        assert aiocache.settings.DEFAULT_POLICY == DefaultPolicy
        assert aiocache.settings.DEFAULT_POLICY_KWARGS == {}

    def test_set_from_dict_str(self):
        config = {
            "CACHE": {
                "class": "aiocache.RedisCache",
                "endpoint": "127.0.0.1",
                "port": 6379
            },
            "SERIALIZER": {
                "class": "aiocache.serializers.DefaultSerializer",
                "random_attr": "random_value"
            },
            "POLICY": {
                "class": "aiocache.policies.DefaultPolicy",
                "max_keys": 2
            }
        }

        aiocache.settings.set_from_dict(config)

        assert aiocache.settings.DEFAULT_CACHE == aiocache.RedisCache
        assert aiocache.settings.DEFAULT_CACHE_KWARGS == {"endpoint": "127.0.0.1", "port": 6379}

        assert aiocache.settings.DEFAULT_SERIALIZER == DefaultSerializer
        assert aiocache.settings.DEFAULT_SERIALIZER_KWARGS == {"random_attr": "random_value"}

        assert aiocache.settings.DEFAULT_POLICY == DefaultPolicy
        assert aiocache.settings.DEFAULT_POLICY_KWARGS == {"max_keys": 2}

    def test_set_defaults_str(self):

        aiocache.settings.set_defaults(
            class_="aiocache.RedisCache", endpoint="127.0.0.1", port=6379)

        assert aiocache.settings.DEFAULT_CACHE == aiocache.RedisCache
        assert aiocache.settings.DEFAULT_CACHE_KWARGS == {"endpoint": "127.0.0.1", "port": 6379}

    def test_set_defaults_str_fail(self):
        with pytest.raises(ValueError):
            aiocache.settings.set_defaults(
                class_="aiocache.serializers.DefaultSerializer", endpoint="127.0.0.1", port=6379)

    def test_set_defaults_class(self):

        aiocache.settings.set_defaults(
            class_=aiocache.RedisCache, endpoint="127.0.0.1", port=6379)

        assert aiocache.settings.DEFAULT_CACHE == aiocache.RedisCache
        assert aiocache.settings.DEFAULT_CACHE_KWARGS == {"endpoint": "127.0.0.1", "port": 6379}

    def test_set_defaults_class_fail(self):

        with pytest.raises(ValueError):
            aiocache.settings.set_defaults(
                class_=DefaultSerializer, endpoint="127.0.0.1", port=6379)

    def test_set_default_serializer_str(self):

        aiocache.settings.set_default_serializer(
            class_="aiocache.serializers.DefaultSerializer", random_attr="random_value")

        assert aiocache.settings.DEFAULT_SERIALIZER == DefaultSerializer
        assert aiocache.settings.DEFAULT_SERIALIZER_KWARGS == {"random_attr": "random_value"}

    def test_set_default_serializer_str_fail(self):

        with pytest.raises(ValueError):
            aiocache.settings.set_default_serializer(
                class_="aiocache.RedisCache", random_attr="random_value")

    def test_set_default_serializer_class(self):

        aiocache.settings.set_default_serializer(
            class_=DefaultSerializer, random_attr="random_value")

        assert aiocache.settings.DEFAULT_SERIALIZER == DefaultSerializer
        assert aiocache.settings.DEFAULT_SERIALIZER_KWARGS == {"random_attr": "random_value"}

    def test_set_default_serializer_class_fail(self):

        with pytest.raises(ValueError):
            aiocache.settings.set_default_serializer(
                class_=aiocache.RedisCache, random_attr="random_value")

    def test_set_default_policy_str(self):

        aiocache.settings.set_default_policy(
            class_="aiocache.policies.DefaultPolicy", max_keys=2)

        assert aiocache.settings.DEFAULT_POLICY == DefaultPolicy
        assert aiocache.settings.DEFAULT_POLICY_KWARGS == {"max_keys": 2}

    def test_set_default_policy_str_fail(self):

        with pytest.raises(ValueError):
            aiocache.settings.set_default_policy(
                class_="aiocache.RedisCache", random_attr="random_value")

    def test_set_default_policy_class(self):

        aiocache.settings.set_default_policy(
            class_=DefaultPolicy, random_attr="random_value")

        assert aiocache.settings.DEFAULT_POLICY == DefaultPolicy
        assert aiocache.settings.DEFAULT_POLICY_KWARGS == {"random_attr": "random_value"}

    def test_set_default_policy_class_fail(self):

        with pytest.raises(ValueError):
            aiocache.settings.set_default_policy(
                class_=aiocache.RedisCache, random_attr="random_value")

    def test_get_defaults(self):

        assert aiocache.settings.get_defaults() == {
            "DEFAULT_CACHE": aiocache.SimpleMemoryCache,
            "DEFAULT_CACHE_KWARGS": {},
            "DEFAULT_SERIALIZER": DefaultSerializer,
            "DEFAULT_SERIALIZER_KWARGS": {},
            "DEFAULT_POLICY": DefaultPolicy,
            "DEFAULT_POLICY_KWARGS": {},
        }
