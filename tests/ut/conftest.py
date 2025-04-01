from contextlib import ExitStack
from unittest.mock import create_autospec, patch

import pytest

from aiocache.plugins import BasePlugin
from ..utils import AbstractBaseCache, ConcreteBaseCache


@pytest.fixture
def mock_cache(mocker):
    return create_autospec(ConcreteBaseCache())


@pytest.fixture
def mock_base_cache():
    """Return BaseCache instance with unimplemented methods mocked out."""
    plugin = create_autospec(BasePlugin, instance=True)
    cache = ConcreteBaseCache(timeout=0.002, plugins=(plugin,))
    methods = (
        "_add",
        "_get",
        "_gets",
        "_set",
        "_multi_get",
        "_multi_set",
        "_delete",
        "_exists",
        "_increment",
        "_expire",
        "_clear",
        "_raw",
        "_close",
        "_redlock_release",
        "acquire_conn",
        "release_conn",
    )
    with ExitStack() as stack:
        for f in methods:
            stack.enter_context(patch.object(cache, f, autospec=True))
        stack.enter_context(patch.object(cache, "_serializer", autospec=True))
        stack.enter_context(patch.object(cache, "build_key", cache._str_build_key))
        yield cache


@pytest.fixture
def abstract_base_cache():
    return AbstractBaseCache()


@pytest.fixture
def base_cache():
    cache = ConcreteBaseCache()
    return cache


@pytest.fixture
async def valkey_cache(valkey_client):
    from aiocache.backends.valkey import ValkeyCache

    async with ValkeyCache(client=valkey_client) as cache:
        yield cache


@pytest.fixture
async def memcached_cache():
    from aiocache.backends.memcached import MemcachedCache

    async with MemcachedCache() as cache:
        yield cache
