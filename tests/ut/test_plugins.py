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
