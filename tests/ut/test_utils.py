import aiocache

from aiocache import RedisCache
from aiocache.utils import get_cache, get_args_dict
from aiocache.serializers import PickleSerializer
from aiocache.plugins import BasePlugin


class TestCacheFactory:

    def test_get_cache(self):
        cache = get_cache(cache=RedisCache)

        assert isinstance(cache, RedisCache)

    def test_get_cache_with_default_config(self):
        aiocache.settings.set_defaults(
            class_="aiocache.RedisCache", endpoint="http://...", port=6379)
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
        aiocache.settings.set_defaults(
            class_="aiocache.RedisCache", endpoint="http://...", port=6379)
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


def test_get_args_dict():

    async def arg_return_dict(keys, dummy=None):
        ret = {}
        for value, key in enumerate(keys or ['a', 'd', 'z', 'y']):
            ret[key] = value
        return ret

    args = ({'b', 'a'},)

    assert get_args_dict(arg_return_dict, args, {}) == {'dummy': None, 'keys': {'a', 'b'}}
    assert get_args_dict(arg_return_dict, args, {'dummy': 'dummy'}) == \
        {'dummy': 'dummy', 'keys': {'a', 'b'}}
    assert get_args_dict(arg_return_dict, [], {'dummy': 'dummy'}) == {'dummy': 'dummy'}
