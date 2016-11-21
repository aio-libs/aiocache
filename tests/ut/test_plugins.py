import pytest
import inspect
import asynctest

from unittest import mock
from aiocache.plugins import BasePlugin, HitMissRatioPlugin
from aiocache.backends import SimpleMemoryBackend


class TestPluginDecorator:

    @pytest.mark.asyncio
    async def test_calls_pre_post(self, mock_cache):
        class TestPlugin(BasePlugin):
            pass
        namespace = "test"
        mock_cache.plugins += [asynctest.Mock(spec=TestPlugin)]
        await mock_cache.clear(namespace=namespace)

        for plugin in mock_cache.plugins:
            plugin.pre_clear.assert_called_with(mock_cache, namespace=namespace)
            plugin.post_clear.assert_called_with(
                mock_cache, namespace=namespace, ret=mock.ANY, took=mock.ANY)

        assert len(mock_cache.plugins) == 2


class TestBasePlugin:

    def test_interface_methods(self):
        for method in BasePlugin._HOOKED_METHODS:
            assert hasattr(BasePlugin, "pre_{}".format(method)) and \
                inspect.iscoroutinefunction(getattr(BasePlugin, "pre_{}".format(method)))
            assert hasattr(BasePlugin, "post_{}".format(method)) and \
                inspect.iscoroutinefunction(getattr(BasePlugin, "pre_{}".format(method)))


class TestHitMissRatioPlugin:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("data, ratio", [
        ({"a": 1, "b": 2, "c": 3}, 0.6),
        ({"a": 1, "z": 0}, 0.2),
        ({}, 0),
        ({"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}, 1)
    ])
    async def test_get_hit_miss_ratio(self, memory_cache, data, ratio):
        keys = ["a", "b", "c", "d", "e", "f"]
        memory_cache.plugins = [HitMissRatioPlugin()]
        SimpleMemoryBackend._cache = data

        for key in keys:
            await memory_cache.get(key)

        hits = [x for x in keys if x in data]
        miss = [x for x in keys if x not in data]
        assert memory_cache.hit_miss_ratio["hits"] == len(hits)
        assert memory_cache.hit_miss_ratio["miss"] == len(miss)
        assert memory_cache.hit_miss_ratio["hit_ratio"] == \
            len(hits)/memory_cache.hit_miss_ratio["total"]
        assert memory_cache.hit_miss_ratio["miss_ratio"] == \
            len(miss)/memory_cache.hit_miss_ratio["total"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("data, ratio", [
        ({"a": 1, "b": 2, "c": 3}, 0.6),
        ({"a": 1, "z": 0}, 0.2),
        ({}, 0),
        ({"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}, 1)
    ])
    async def test_multi_get_hit_miss_ratio(self, memory_cache, data, ratio):
        keys = ["a", "b", "c", "d", "e", "f"]
        memory_cache.plugins = [HitMissRatioPlugin()]
        SimpleMemoryBackend._cache = data

        for key in keys:
            await memory_cache.multi_get([key])

        hits = [x for x in keys if x in data]
        assert memory_cache.hit_miss_ratio["hits"] == len(hits)
        assert memory_cache.hit_miss_ratio["hit_ratio"] == \
            len(hits)/memory_cache.hit_miss_ratio["total"]
