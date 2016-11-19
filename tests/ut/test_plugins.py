import pytest
import inspect

from unittest import mock
from aiocache.plugins import BasePlugin


class TestPluginDecorator:

    @pytest.mark.asyncio
    async def test_calls_pre_post(self, mock_cache):
        namespace = "test"
        await mock_cache.clear(namespace=namespace)

        for plugin in mock_cache.plugins:
            plugin.pre_clear.assert_called_with(mock_cache, namespace=namespace)
            plugin.post_clear.assert_called_with(
                mock_cache, namespace=namespace, took=mock.ANY)


class TestBasePlugin:

    def test_interface_methods(self):
        for method in BasePlugin._HOOKED_METHODS:
            assert hasattr(BasePlugin, "pre_{}".format(method)) and \
                inspect.iscoroutinefunction(getattr(BasePlugin, "pre_{}".format(method)))
            assert hasattr(BasePlugin, "post_{}".format(method)) and \
                inspect.iscoroutinefunction(getattr(BasePlugin, "pre_{}".format(method)))
