from unittest.mock import create_autospec

import pytest

from aiocache.base import API, BaseCache
from aiocache.plugins import BasePlugin, HitMissRatioPlugin, TimingPlugin
from ..utils import Keys


class TestBasePlugin:
    async def test_interface_methods(self):
        for method in API.CMDS:
            pre = await getattr(BasePlugin, "pre_{}".format(method.__name__))(None)
            assert pre is None
            post = await getattr(BasePlugin, "post_{}".format(method.__name__))(None)
            assert post is None

    async def test_do_nothing(self):
        assert await BasePlugin().do_nothing() is None


class TestTimingPlugin:
    async def test_save_time(self, mock_cache):
        do_save_time = TimingPlugin().save_time("get")
        await do_save_time("self", mock_cache, took=1)
        await do_save_time("self", mock_cache, took=2)

        assert mock_cache.profiling["get_total"] == 2
        assert mock_cache.profiling["get_max"] == 2
        assert mock_cache.profiling["get_min"] == 1
        assert mock_cache.profiling["get_avg"] == 1.5

    async def test_save_time_post_set(self, mock_cache):
        await TimingPlugin().post_set(mock_cache, took=1)
        await TimingPlugin().post_set(mock_cache, took=2)

        assert mock_cache.profiling["set_total"] == 2
        assert mock_cache.profiling["set_max"] == 2
        assert mock_cache.profiling["set_min"] == 1
        assert mock_cache.profiling["set_avg"] == 1.5

    async def test_interface_methods(self):
        for method in API.CMDS:
            assert hasattr(TimingPlugin, "pre_{}".format(method.__name__))
            assert hasattr(TimingPlugin, "post_{}".format(method.__name__))


class TestHitMissRatioPlugin:
    @pytest.fixture
    def plugin(self):
        return HitMissRatioPlugin()

    async def test_post_get(self, plugin):
        client = create_autospec(BaseCache, instance=True)
        await plugin.post_get(client, Keys.KEY)

        assert client.hit_miss_ratio["hits"] == 0
        assert client.hit_miss_ratio["total"] == 1
        assert client.hit_miss_ratio["hit_ratio"] == 0

        await plugin.post_get(client, Keys.KEY, ret="value")
        assert client.hit_miss_ratio["hits"] == 1
        assert client.hit_miss_ratio["total"] == 2
        assert client.hit_miss_ratio["hit_ratio"] == 0.5

    async def test_post_multi_get(self, plugin):
        client = create_autospec(BaseCache, instance=True)
        await plugin.post_multi_get(client, [Keys.KEY, Keys.KEY_1], ret=[None, None])

        assert client.hit_miss_ratio["hits"] == 0
        assert client.hit_miss_ratio["total"] == 2
        assert client.hit_miss_ratio["hit_ratio"] == 0

        await plugin.post_multi_get(client, [Keys.KEY, Keys.KEY_1], ret=["value", "random"])
        assert client.hit_miss_ratio["hits"] == 2
        assert client.hit_miss_ratio["total"] == 4
        assert client.hit_miss_ratio["hit_ratio"] == 0.5
