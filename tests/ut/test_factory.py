from unittest.mock import Mock, patch

import pytest

from aiocache import AIOCACHE_CACHES, Cache, caches
from aiocache.backends.memcached import MemcachedCache
from aiocache.backends.memory import SimpleMemoryCache
from aiocache.backends.redis import RedisCache
from aiocache.exceptions import InvalidCacheType
from aiocache.factory import _class_from_string, _create_cache
from aiocache.plugins import HitMissRatioPlugin, TimingPlugin
from aiocache.serializers import JsonSerializer, PickleSerializer

assert Cache.REDIS is not None
assert Cache.MEMCACHED is not None
CACHE_NAMES = (Cache.MEMORY.NAME, Cache.REDIS.NAME, Cache.MEMCACHED.NAME)


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
        serializer={"class": PickleSerializer, "encoding": "encoding"},
        plugins=[{"class": "aiocache.plugins.TimingPlugin"}],
    )

    assert isinstance(redis.serializer, PickleSerializer)
    assert redis.serializer.encoding == "encoding"
    assert isinstance(redis.plugins[0], TimingPlugin)


class TestCache:
    def test_cache_types(self):
        assert Cache.MEMORY == SimpleMemoryCache
        assert Cache.REDIS == RedisCache
        assert Cache.MEMCACHED == MemcachedCache

    @pytest.mark.parametrize("cache_type", CACHE_NAMES)
    def test_new(self, cache_type):
        kwargs = {"a": 1, "b": 2}
        cache_class = Cache.get_scheme_class(cache_type)

        with patch("aiocache.{}.__init__".format(cache_class.__name__)) as init:
            cache = Cache(cache_class, **kwargs)
            assert isinstance(cache, cache_class)
            init.assert_called_once_with(**kwargs)

    def test_new_defaults_to_memory(self):
        assert isinstance(Cache(), Cache.MEMORY)

    def test_new_invalid_cache_raises(self):
        with pytest.raises(InvalidCacheType) as e:
            Cache(object)
        assert str(e.value) == "Invalid cache type, you can only use {}".format(
            list(AIOCACHE_CACHES.keys())
        )

    @pytest.mark.parametrize("scheme", CACHE_NAMES)
    def test_get_scheme_class(self, scheme):
        assert Cache.get_scheme_class(scheme) == AIOCACHE_CACHES[scheme]

    def test_get_scheme_class_invalid(self):
        with pytest.raises(InvalidCacheType):
            Cache.get_scheme_class("http")

    @pytest.mark.parametrize("scheme", CACHE_NAMES)
    def test_from_url_returns_cache_from_scheme(self, scheme):
        assert isinstance(Cache.from_url("{}://".format(scheme)), Cache.get_scheme_class(scheme))

    @pytest.mark.parametrize(
        "url,expected_args",
        [
            ("redis://", {}),
            ("redis://localhost", {"endpoint": "localhost"}),
            ("redis://localhost/", {"endpoint": "localhost"}),
            ("redis://localhost:6379", {"endpoint": "localhost", "port": 6379}),
            (
                "redis://localhost/?arg1=arg1&arg2=arg2",
                {"endpoint": "localhost", "arg1": "arg1", "arg2": "arg2"},
            ),
            (
                "redis://localhost:6379/?arg1=arg1&arg2=arg2",
                {"endpoint": "localhost", "port": 6379, "arg1": "arg1", "arg2": "arg2"},
            ),
            ("redis:///?arg1=arg1", {"arg1": "arg1"}),
            ("redis:///?arg2=arg2", {"arg2": "arg2"}),
            (
                "redis://:password@localhost:6379",
                {"endpoint": "localhost", "password": "password", "port": 6379},
            ),
            (
                "redis://:password@localhost:6379?password=pass",
                {"endpoint": "localhost", "password": "password", "port": 6379},
            ),
        ],
    )
    def test_from_url_calls_cache_with_args(self, url, expected_args):
        with patch("aiocache.factory.Cache") as mock:
            Cache.from_url(url)

        mock.assert_called_once_with(mock.get_scheme_class.return_value, **expected_args)

    def test_calls_parse_uri_path_from_cache(self):
        with patch("aiocache.factory.Cache") as mock:
            mock.get_scheme_class.return_value.parse_uri_path = Mock(return_value={"arg1": "arg1"})
            Cache.from_url("redis:///")

        mock.get_scheme_class.return_value.parse_uri_path.assert_called_once_with("/")
        mock.assert_called_once_with(mock.get_scheme_class.return_value, arg1="arg1")

    def test_from_url_invalid_protocol(self):
        with pytest.raises(InvalidCacheType):
            Cache.from_url("http://")


class TestCacheHandler:
    @pytest.fixture(autouse=True)
    def remove_caches(self):
        caches._caches = {}

    def test_add_new_entry(self):
        alias = "memory"
        config = {
            "cache": "aiocache.SimpleMemoryCache",
            "serializer": {"class": "aiocache.serializers.StringSerializer"},
        }
        caches.add(alias, config)

        assert caches.get_config()[alias] == config

    def test_add_updates_existing_entry(self):
        alias = "memory"
        config = {
            "cache": "aiocache.SimpleMemoryCache",
            "serializer": {"class": "aiocache.serializers.StringSerializer"},
        }
        caches.add(alias, {})
        caches.add(alias, config)

        assert caches.get_config()[alias] == config

    def test_get_wrong_alias(self):
        with pytest.raises(KeyError):
            caches.get("wrong_cache")

        with pytest.raises(KeyError):
            caches.create("wrong_cache")

    def test_reuse_instance(self):
        assert caches.get("default") is caches.get("default")

    def test_create_not_reuse(self):
        assert caches.create("default") is not caches.create("default")

    def test_create_extra_args(self):
        caches.set_config(
            {
                "default": {
                    "cache": "aiocache.RedisCache",
                    "endpoint": "127.0.0.9",
                    "db": 10,
                    "port": 6378,
                }
            }
        )
        cache = caches.create("default", namespace="whatever", endpoint="127.0.0.10", db=10)
        assert cache.namespace == "whatever"
        assert cache.endpoint == "127.0.0.10"
        assert cache.db == 10

    def test_create_deprecated(self):
        with patch("aiocache.factory.warnings.warn") as mock:
            caches.create(cache="aiocache.SimpleMemoryCache")

        mock.assert_called_once_with(
            "Creating a cache with an explicit config is deprecated, use 'aiocache.Cache'",
            DeprecationWarning,
        )

    def test_retrieve_cache(self):
        caches.set_config(
            {
                "default": {
                    "cache": "aiocache.RedisCache",
                    "endpoint": "127.0.0.10",
                    "port": 6378,
                    "ttl": 10,
                    "serializer": {
                        "class": "aiocache.serializers.PickleSerializer",
                        "encoding": "encoding",
                    },
                    "plugins": [
                        {"class": "aiocache.plugins.HitMissRatioPlugin"},
                        {"class": "aiocache.plugins.TimingPlugin"},
                    ],
                }
            }
        )

        cache = caches.get("default")
        assert isinstance(cache, RedisCache)
        assert cache.endpoint == "127.0.0.10"
        assert cache.port == 6378
        assert cache.ttl == 10
        assert isinstance(cache.serializer, PickleSerializer)
        assert cache.serializer.encoding == "encoding"
        assert len(cache.plugins) == 2

    def test_retrieve_cache_new_instance(self):
        caches.set_config(
            {
                "default": {
                    "cache": "aiocache.RedisCache",
                    "endpoint": "127.0.0.10",
                    "port": 6378,
                    "serializer": {
                        "class": "aiocache.serializers.PickleSerializer",
                        "encoding": "encoding",
                    },
                    "plugins": [
                        {"class": "aiocache.plugins.HitMissRatioPlugin"},
                        {"class": "aiocache.plugins.TimingPlugin"},
                    ],
                }
            }
        )

        cache = caches.create("default")
        assert isinstance(cache, RedisCache)
        assert cache.endpoint == "127.0.0.10"
        assert cache.port == 6378
        assert isinstance(cache.serializer, PickleSerializer)
        assert cache.serializer.encoding == "encoding"
        assert len(cache.plugins) == 2

    def test_create_cache_str_no_alias(self):
        cache = caches.create(cache="aiocache.RedisCache")

        assert isinstance(cache, RedisCache)
        assert cache.endpoint == "127.0.0.1"
        assert cache.port == 6379

    def test_create_cache_class_no_alias(self):
        cache = caches.create(cache=RedisCache)

        assert isinstance(cache, RedisCache)
        assert cache.endpoint == "127.0.0.1"
        assert cache.port == 6379

    def test_create_cache_ensure_alias_or_cache(self):
        with pytest.raises(TypeError):
            caches.create()

    def test_alias_config_is_reusable(self):
        caches.set_config(
            {
                "default": {
                    "cache": "aiocache.RedisCache",
                    "endpoint": "127.0.0.10",
                    "port": 6378,
                    "serializer": {"class": "aiocache.serializers.PickleSerializer"},
                    "plugins": [
                        {"class": "aiocache.plugins.HitMissRatioPlugin"},
                        {"class": "aiocache.plugins.TimingPlugin"},
                    ],
                },
                "alt": {"cache": "aiocache.SimpleMemoryCache"},
            }
        )

        default = caches.create(**caches.get_alias_config("default"))
        alt = caches.create(**caches.get_alias_config("alt"))

        assert isinstance(default, RedisCache)
        assert default.endpoint == "127.0.0.10"
        assert default.port == 6378
        assert isinstance(default.serializer, PickleSerializer)
        assert len(default.plugins) == 2

        assert isinstance(alt, SimpleMemoryCache)

    def test_multiple_caches(self):
        caches.set_config(
            {
                "default": {
                    "cache": "aiocache.RedisCache",
                    "endpoint": "127.0.0.10",
                    "port": 6378,
                    "serializer": {"class": "aiocache.serializers.PickleSerializer"},
                    "plugins": [
                        {"class": "aiocache.plugins.HitMissRatioPlugin"},
                        {"class": "aiocache.plugins.TimingPlugin"},
                    ],
                },
                "alt": {"cache": "aiocache.SimpleMemoryCache"},
            }
        )

        default = caches.get("default")
        alt = caches.get("alt")

        assert isinstance(default, RedisCache)
        assert default.endpoint == "127.0.0.10"
        assert default.port == 6378
        assert isinstance(default.serializer, PickleSerializer)
        assert len(default.plugins) == 2

        assert isinstance(alt, SimpleMemoryCache)

    def test_default_caches(self):
        assert caches.get_config() == {
            "default": {
                "cache": "aiocache.SimpleMemoryCache",
                "serializer": {"class": "aiocache.serializers.NullSerializer"},
            }
        }

    def test_get_alias_config(self):
        assert caches.get_alias_config("default") == {
            "cache": "aiocache.SimpleMemoryCache",
            "serializer": {"class": "aiocache.serializers.NullSerializer"},
        }

    def test_set_empty_config(self):
        with pytest.raises(ValueError):
            caches.set_config({})

    def test_set_config_updates_existing_values(self):
        assert not isinstance(caches.get("default").serializer, JsonSerializer)
        caches.set_config(
            {
                "default": {
                    "cache": "aiocache.SimpleMemoryCache",
                    "serializer": {"class": "aiocache.serializers.JsonSerializer"},
                }
            }
        )
        assert isinstance(caches.get("default").serializer, JsonSerializer)

    def test_set_config_removes_existing_caches(self):
        caches.set_config(
            {
                "default": {"cache": "aiocache.SimpleMemoryCache"},
                "alt": {"cache": "aiocache.SimpleMemoryCache"},
            }
        )
        caches.get("default")
        caches.get("alt")
        assert len(caches._caches) == 2

        caches.set_config(
            {
                "default": {"cache": "aiocache.SimpleMemoryCache"},
                "alt": {"cache": "aiocache.SimpleMemoryCache"},
            }
        )
        assert caches._caches == {}

    def test_set_config_no_default(self):
        with pytest.raises(ValueError):
            caches.set_config(
                {
                    "no_default": {
                        "cache": "aiocache.RedisCache",
                        "endpoint": "127.0.0.10",
                        "port": 6378,
                        "serializer": {"class": "aiocache.serializers.PickleSerializer"},
                        "plugins": [
                            {"class": "aiocache.plugins.HitMissRatioPlugin"},
                            {"class": "aiocache.plugins.TimingPlugin"},
                        ],
                    }
                }
            )

    def test_ensure_plugins_order(self):
        caches.set_config(
            {
                "default": {
                    "cache": "aiocache.RedisCache",
                    "plugins": [
                        {"class": "aiocache.plugins.HitMissRatioPlugin"},
                        {"class": "aiocache.plugins.TimingPlugin"},
                    ],
                }
            }
        )

        cache = caches.get("default")
        assert isinstance(cache.plugins[0], HitMissRatioPlugin)

        cache = caches.create("default")
        assert isinstance(cache.plugins[0], HitMissRatioPlugin)
