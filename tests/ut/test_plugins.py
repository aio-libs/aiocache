import pytest
import inspect
import asynctest

from unittest import mock
from aiocache.plugins import BasePlugin, save_time


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


@pytest.mark.asyncio
async def test_save_time(mock_cache):
    do_save_time = save_time('get')
    await do_save_time('self', mock_cache, took=1)
    await do_save_time('self', mock_cache, took=2)

    assert mock_cache.profiling["get_total"] == 2
    assert mock_cache.profiling["get_max"] == 2
    assert mock_cache.profiling["get_min"] == 1
    assert mock_cache.profiling["get_avg"] == 1.5
