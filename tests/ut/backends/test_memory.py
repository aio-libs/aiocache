import asyncio
from unittest.mock import ANY, MagicMock, create_autospec, patch

import pytest
from tests.utils import Keys

from aiocache.backends.memory import SimpleMemoryBackend, SimpleMemoryCache
from aiocache.base import BaseCache
from aiocache.serializers import NullSerializer


@pytest.fixture
def memory(mocker):
    SimpleMemoryBackend._handlers = {}
    SimpleMemoryBackend._cache = {}
    mocker.spy(SimpleMemoryBackend, "_cache")
    return SimpleMemoryBackend()


class TestSimpleMemoryBackend:
    async def test_get(self, memory):
        await memory._get(Keys.KEY)
        SimpleMemoryBackend._cache.get.assert_called_with(Keys.KEY)

    async def test_gets(self, mocker, memory):
        mocker.spy(memory, "_get")
        await memory._gets(Keys.KEY)
        memory._get.assert_called_with(Keys.KEY, encoding="utf-8", _conn=ANY)

    async def test_set(self, memory):
        await memory._set(Keys.KEY, "value")
        SimpleMemoryBackend._cache.__setitem__.assert_called_with(Keys.KEY, "value")

    async def test_set_no_ttl_no_handle(self, memory):
        await memory._set(Keys.KEY, "value", ttl=0)
        assert Keys.KEY not in memory._handlers

        await memory._set(Keys.KEY, "value")
        assert Keys.KEY not in memory._handlers

    async def test_set_cancel_previous_ttl_handle(self, memory):
        await memory._set(Keys.KEY, "value", ttl=0.1)
        memory._handlers[Keys.KEY].cancel.assert_not_called()

        await memory._set(Keys.KEY, "new_value", ttl=0.1)
        memory._handlers[Keys.KEY].cancel.assert_called_once_with()

    async def test_set_ttl_handle(self, memory):
        await memory._set(Keys.KEY, "value", ttl=100)
        assert Keys.KEY in memory._handlers
        assert isinstance(memory._handlers[Keys.KEY], asyncio.Handle)

    async def test_set_cas_token(self, memory):
        memory._cache.get.return_value = "old_value"
        assert await memory._set(Keys.KEY, "value", _cas_token="old_value") == 1
        SimpleMemoryBackend._cache.__setitem__.assert_called_with(Keys.KEY, "value")

    async def test_set_cas_fail(self, memory):
        memory._cache.get.return_value = "value"
        assert await memory._set(Keys.KEY, "value", _cas_token="old_value") == 0
        assert SimpleMemoryBackend._cache.__setitem__.call_count == 0

    async def test_multi_get(self, memory):
        await memory._multi_get([Keys.KEY, Keys.KEY_1])
        SimpleMemoryBackend._cache.get.assert_any_call(Keys.KEY)
        SimpleMemoryBackend._cache.get.assert_any_call(Keys.KEY_1)

    async def test_multi_set(self, memory):
        await memory._multi_set([(Keys.KEY, "value"), (Keys.KEY_1, "random")])
        SimpleMemoryBackend._cache.__setitem__.assert_any_call(Keys.KEY, "value")
        SimpleMemoryBackend._cache.__setitem__.assert_any_call(Keys.KEY_1, "random")

    async def test_add(self, memory, mocker):
        mocker.spy(memory, "_set")
        await memory._add(Keys.KEY, "value")
        memory._set.assert_called_with(Keys.KEY, "value", ttl=None)

    async def test_add_existing(self, memory):
        SimpleMemoryBackend._cache.__contains__.return_value = True
        with pytest.raises(ValueError):
            await memory._add(Keys.KEY, "value")

    async def test_exists(self, memory):
        await memory._exists(Keys.KEY)
        SimpleMemoryBackend._cache.__contains__.assert_called_with(Keys.KEY)

    async def test_increment(self, memory):
        await memory._increment(Keys.KEY, 2)
        SimpleMemoryBackend._cache.__contains__.assert_called_with(Keys.KEY)
        SimpleMemoryBackend._cache.__setitem__.assert_called_with(Keys.KEY, 2)

    async def test_increment_missing(self, memory):
        SimpleMemoryBackend._cache.__contains__.return_value = True
        SimpleMemoryBackend._cache.__getitem__.return_value = 2
        await memory._increment(Keys.KEY, 2)
        SimpleMemoryBackend._cache.__getitem__.assert_called_with(Keys.KEY)
        SimpleMemoryBackend._cache.__setitem__.assert_called_with(Keys.KEY, 4)

    async def test_increment_typerror(self, memory):
        SimpleMemoryBackend._cache.__contains__.return_value = True
        SimpleMemoryBackend._cache.__getitem__.return_value = "asd"
        with pytest.raises(TypeError):
            await memory._increment(Keys.KEY, 2)

    async def test_expire_no_handle_no_ttl(self, memory):
        SimpleMemoryBackend._cache.__contains__.return_value = True
        await memory._expire(Keys.KEY, 0)
        assert memory._handlers.get(Keys.KEY) is None

    async def test_expire_no_handle_ttl(self, memory):
        SimpleMemoryBackend._cache.__contains__.return_value = True
        await memory._expire(Keys.KEY, 1)
        assert isinstance(memory._handlers.get(Keys.KEY), asyncio.Handle)

    async def test_expire_handle_ttl(self, memory):
        fake = create_autospec(asyncio.TimerHandle, instance=True)
        SimpleMemoryBackend._handlers[Keys.KEY] = fake
        SimpleMemoryBackend._cache.__contains__.return_value = True
        await memory._expire(Keys.KEY, 1)
        assert fake.cancel.call_count == 1
        assert isinstance(memory._handlers.get(Keys.KEY), asyncio.Handle)

    async def test_expire_missing(self, memory):
        SimpleMemoryBackend._cache.__contains__.return_value = False
        assert await memory._expire(Keys.KEY, 1) is False

    async def test_delete(self, memory):
        fake = create_autospec(asyncio.TimerHandle, instance=True)
        SimpleMemoryBackend._handlers[Keys.KEY] = fake
        await memory._delete(Keys.KEY)
        assert fake.cancel.call_count == 1
        assert Keys.KEY not in SimpleMemoryBackend._handlers
        SimpleMemoryBackend._cache.pop.assert_called_with(Keys.KEY, None)

    async def test_delete_missing(self, memory):
        SimpleMemoryBackend._cache.pop.return_value = None
        await memory._delete(Keys.KEY)
        SimpleMemoryBackend._cache.pop.assert_called_with(Keys.KEY, None)

    async def test_delete_non_truthy(self, memory):
        non_truthy = MagicMock(spec_set=("__bool__",))
        non_truthy.__bool__.side_effect = ValueError("Does not implement truthiness")

        with pytest.raises(ValueError):
            bool(non_truthy)

        SimpleMemoryBackend._cache.pop.return_value = non_truthy
        await memory._delete(Keys.KEY)

        assert non_truthy.__bool__.call_count == 1
        SimpleMemoryBackend._cache.pop.assert_called_with(Keys.KEY, None)

    async def test_clear_namespace(self, memory):
        SimpleMemoryBackend._cache.__iter__.return_value = iter(["nma", "nmb", "no"])
        await memory._clear("nm")
        assert SimpleMemoryBackend._cache.pop.call_count == 2
        SimpleMemoryBackend._cache.pop.assert_any_call("nma", None)
        SimpleMemoryBackend._cache.pop.assert_any_call("nmb", None)

    async def test_clear_no_namespace(self, memory):
        SimpleMemoryBackend._handlers = "asdad"
        SimpleMemoryBackend._cache = "asdad"
        await memory._clear()
        SimpleMemoryBackend._handlers = {}
        SimpleMemoryBackend._cache = {}

    async def test_raw(self, memory):
        await memory._raw("get", Keys.KEY)
        SimpleMemoryBackend._cache.get.assert_called_with(Keys.KEY)

        await memory._set(Keys.KEY, "value")
        SimpleMemoryBackend._cache.__setitem__.assert_called_with(Keys.KEY, "value")

    async def test_redlock_release(self, memory):
        SimpleMemoryBackend._cache.get.return_value = "lock"
        assert await memory._redlock_release(Keys.KEY, "lock") == 1
        SimpleMemoryBackend._cache.get.assert_called_with(Keys.KEY)
        SimpleMemoryBackend._cache.pop.assert_called_with(Keys.KEY)

    async def test_redlock_release_nokey(self, memory):
        SimpleMemoryBackend._cache.get.return_value = None
        assert await memory._redlock_release(Keys.KEY, "lock") == 0
        SimpleMemoryBackend._cache.get.assert_called_with(Keys.KEY)
        assert SimpleMemoryBackend._cache.pop.call_count == 0


class TestSimpleMemoryCache:
    def test_name(self):
        assert SimpleMemoryCache.NAME == "memory"

    def test_inheritance(self):
        assert isinstance(SimpleMemoryCache(), BaseCache)

    def test_default_serializer(self):
        assert isinstance(SimpleMemoryCache().serializer, NullSerializer)

    def test_parse_uri_path(self):
        assert SimpleMemoryCache().parse_uri_path("/1/2/3") == {}
