import pytest
import inspect

from unittest.mock import MagicMock

from aiocache.plugins import BasePlugin, HitMissRatioPlugin, save_time, do_nothing
from aiocache.cache import API, BaseCache


class TestBasePlugin:

    def test_interface_methods(self):
        for method in API.CMDS:
            assert hasattr(BasePlugin, "pre_{}".format(method.__name__)) and \
                inspect.iscoroutinefunction(getattr(BasePlugin, "pre_{}".format(method.__name__)))
            assert hasattr(BasePlugin, "post_{}".format(method.__name__)) and \
                inspect.iscoroutinefunction(getattr(BasePlugin, "pre_{}".format(method.__name__)))


@pytest.mark.asyncio
async def test_do_nothing():
    assert await do_nothing(MagicMock(), MagicMock()) is None


@pytest.mark.asyncio
async def test_save_time(mock_cache):
    do_save_time = save_time('get')
    await do_save_time('self', mock_cache, took=1)
    await do_save_time('self', mock_cache, took=2)

    assert mock_cache.profiling["get_total"] == 2
    assert mock_cache.profiling["get_max"] == 2
    assert mock_cache.profiling["get_min"] == 1
    assert mock_cache.profiling["get_avg"] == 1.5


class TestHitMissRatioPlugin:

    @pytest.fixture
    def plugin(self):
        return HitMissRatioPlugin()

    @pytest.mark.asyncio
    async def test_post_get(self, plugin):
        client = MagicMock(spec=BaseCache)
        await plugin.post_get(client, pytest.KEY)

        assert client.hit_miss_ratio['hits'] == 0
        assert client.hit_miss_ratio["total"] == 1
        assert client.hit_miss_ratio['hit_ratio'] == 0

        await plugin.post_get(client, pytest.KEY, ret="value")
        assert client.hit_miss_ratio['hits'] == 1
        assert client.hit_miss_ratio["total"] == 2
        assert client.hit_miss_ratio['hit_ratio'] == 0.5

    @pytest.mark.asyncio
    async def test_post_multi_get(self, plugin):
        client = MagicMock(spec=BaseCache)
        await plugin.post_multi_get(client, [pytest.KEY, pytest.KEY_1], ret=[None, "random"])

        assert client.hit_miss_ratio['hits'] == 1
        assert client.hit_miss_ratio["total"] == 2
        assert client.hit_miss_ratio['hit_ratio'] == 0.5
