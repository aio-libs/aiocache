import asyncio
import pickle
from unittest.mock import ANY, MagicMock, create_autospec, patch

import pytest

from aiocache.backends.memory import SimpleMemoryCache
from aiocache.base import BaseCache
from aiocache.serializers import NullSerializer, PickleSerializer
from ...utils import Keys


@pytest.fixture
def memory(mocker):
    memory = SimpleMemoryCache()
    mocker.spy(memory, "_cache")
    return memory


class TestSimpleMemoryCache:
    async def test_get(self, memory):
        await memory._get(Keys.KEY)
        memory._cache.get.assert_called_with(Keys.KEY)

    async def test_gets(self, mocker, memory):
        mocker.spy(memory, "_get")
        await memory._gets(Keys.KEY)
        memory._get.assert_called_with(Keys.KEY, encoding="utf-8", _conn=ANY)

    async def test_set(self, memory):
        await memory._set(Keys.KEY, "value")
        memory._cache.__setitem__.assert_called_with(Keys.KEY, "value")

    async def test_set_no_ttl_no_handle(self, memory):
        await memory._set(Keys.KEY, "value", ttl=0)
        assert Keys.KEY not in memory._handlers

        await memory._set(Keys.KEY, "value")
        assert Keys.KEY not in memory._handlers

    async def test_set_cancel_previous_ttl_handle(self, memory):
        with patch("asyncio.get_running_loop", autospec=True):
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
        memory._cache.__setitem__.assert_called_with(Keys.KEY, "value")

    async def test_set_cas_fail(self, memory):
        memory._cache.get.return_value = "value"
        assert await memory._set(Keys.KEY, "value", _cas_token="old_value") == 0
        assert memory._cache.__setitem__.call_count == 0

    async def test_multi_get(self, memory):
        await memory._multi_get([Keys.KEY, Keys.KEY_1])
        memory._cache.get.assert_any_call(Keys.KEY)
        memory._cache.get.assert_any_call(Keys.KEY_1)

    async def test_multi_set(self, memory):
        await memory._multi_set([(Keys.KEY, "value"), (Keys.KEY_1, "random")])
        memory._cache.__setitem__.assert_any_call(Keys.KEY, "value")
        memory._cache.__setitem__.assert_any_call(Keys.KEY_1, "random")

    async def test_add(self, memory, mocker):
        mocker.spy(memory, "_set")
        await memory._add(Keys.KEY, "value")
        memory._set.assert_called_with(Keys.KEY, "value", ttl=None)

    async def test_add_existing(self, memory):
        memory._cache.__contains__.return_value = True
        with pytest.raises(ValueError):
            await memory._add(Keys.KEY, "value")

    async def test_exists(self, memory):
        await memory._exists(Keys.KEY)
        memory._cache.__contains__.assert_called_with(Keys.KEY)

    async def test_increment(self, memory):
        await memory._increment(Keys.KEY, 2)
        memory._cache.__contains__.assert_called_with(Keys.KEY)
        memory._cache.__setitem__.assert_called_with(Keys.KEY, 2)

    async def test_increment_missing(self, memory):
        memory._cache.__contains__.return_value = True
        memory._cache.__getitem__.return_value = 2
        await memory._increment(Keys.KEY, 2)
        memory._cache.__getitem__.assert_called_with(Keys.KEY)
        memory._cache.__setitem__.assert_called_with(Keys.KEY, 4)

    async def test_increment_typerror(self, memory):
        memory._cache.__contains__.return_value = True
        memory._cache.__getitem__.return_value = "asd"
        with pytest.raises(TypeError):
            await memory._increment(Keys.KEY, 2)

    async def test_expire_no_handle_no_ttl(self, memory):
        memory._cache.__contains__.return_value = True
        await memory._expire(Keys.KEY, 0)
        assert memory._handlers.get(Keys.KEY) is None

    async def test_expire_no_handle_ttl(self, memory):
        memory._cache.__contains__.return_value = True
        await memory._expire(Keys.KEY, 1)
        assert isinstance(memory._handlers.get(Keys.KEY), asyncio.Handle)

    async def test_expire_handle_ttl(self, memory):
        fake = create_autospec(asyncio.TimerHandle, instance=True)
        memory._handlers[Keys.KEY] = fake
        memory._cache.__contains__.return_value = True
        await memory._expire(Keys.KEY, 1)
        assert fake.cancel.call_count == 1
        assert isinstance(memory._handlers.get(Keys.KEY), asyncio.Handle)

    async def test_expire_missing(self, memory):
        memory._cache.__contains__.return_value = False
        assert await memory._expire(Keys.KEY, 1) is False

    async def test_delete(self, memory):
        fake = create_autospec(asyncio.TimerHandle, instance=True)
        memory._handlers[Keys.KEY] = fake
        await memory._delete(Keys.KEY)
        assert fake.cancel.call_count == 1
        assert Keys.KEY not in memory._handlers
        memory._cache.pop.assert_called_with(Keys.KEY, None)

    async def test_delete_missing(self, memory):
        memory._cache.pop.return_value = None
        await memory._delete(Keys.KEY)
        memory._cache.pop.assert_called_with(Keys.KEY, None)

    async def test_delete_non_truthy(self, memory):
        non_truthy = MagicMock(spec_set=("__bool__",))
        non_truthy.__bool__.side_effect = ValueError("Does not implement truthiness")

        with pytest.raises(ValueError):
            bool(non_truthy)

        memory._cache.pop.return_value = non_truthy
        await memory._delete(Keys.KEY)

        assert non_truthy.__bool__.call_count == 1
        memory._cache.pop.assert_called_with(Keys.KEY, None)

    async def test_multi_delete(self, memory):
        memory._cache.pop.side_effect = ["value1", None, "value3"]
        result = await memory._multi_delete([Keys.KEY, Keys.KEY_1, Keys.KEY_2])
        assert result == 2
        memory._cache.pop.assert_any_call(Keys.KEY, None)
        memory._cache.pop.assert_any_call(Keys.KEY_1, None)
        memory._cache.pop.assert_any_call(Keys.KEY_2, None)

    async def test_multi_delete_empty_list(self, memory):
        result = await memory._multi_delete([])
        assert result == 0
        memory._cache.pop.assert_not_called()

    async def test_clear_namespace(self, memory):
        memory._cache.__iter__.return_value = iter(["nma", "nmb", "no"])
        await memory._clear("nm")
        assert memory._cache.pop.call_count == 2
        memory._cache.pop.assert_any_call("nma", None)
        memory._cache.pop.assert_any_call("nmb", None)

    async def test_clear_no_namespace(self, memory):
        memory._handlers = "asdad"
        memory._cache = "asdad"
        await memory._clear()
        memory._handlers = {}
        memory._cache = {}

    async def test_raw(self, memory):
        await memory._raw("get", Keys.KEY)
        memory._cache.get.assert_called_with(Keys.KEY)

        await memory._set(Keys.KEY, "value")
        memory._cache.__setitem__.assert_called_with(Keys.KEY, "value")

    async def test_redlock_release(self, memory):
        memory._cache.get.return_value = "lock"
        fake = create_autospec(asyncio.TimerHandle, instance=True)
        memory._handlers[Keys.KEY] = fake
        assert await memory._redlock_release(Keys.KEY, "lock") == 1
        memory._cache.get.assert_called_with(Keys.KEY)
        memory._cache.pop.assert_called_with(Keys.KEY, None)
        assert fake.cancel.call_count == 1
        assert Keys.KEY not in memory._handlers

    async def test_redlock_release_nokey(self, memory):
        memory._cache.get.return_value = None
        assert await memory._redlock_release(Keys.KEY, "lock") == 0
        memory._cache.get.assert_called_with(Keys.KEY)
        assert memory._cache.pop.call_count == 0

    def test_name(self):
        assert SimpleMemoryCache.NAME == "memory"

    def test_inheritance(self):
        assert isinstance(SimpleMemoryCache(), BaseCache)

    def test_default_serializer(self):
        assert isinstance(SimpleMemoryCache().serializer, NullSerializer)

    def test_parse_uri_path(self):
        assert SimpleMemoryCache().parse_uri_path("/1/2/3") == {}

    async def test_maxsize_enforcement(self):
        cache = SimpleMemoryCache(maxsize=2)

        # Fill cache to maxsize
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        assert await cache.exists("key1")
        assert await cache.exists("key2")
        assert len(cache._cache) == 2

        # Add third item - should evict key1 (LRU)
        await cache.set("key3", "value3")
        assert not await cache.exists("key1")
        assert await cache.exists("key2")
        assert await cache.exists("key3")
        assert len(cache._cache) == 2

    async def test_eviction_order(self):
        cache = SimpleMemoryCache(maxsize=3)

        # Add initial items
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Access key1 to make it recently used
        await cache.get("key1")

        # Add fourth item - should evict key2 (least recently used)
        await cache.set("key4", "value4")
        assert await cache.exists("key1")
        assert not await cache.exists("key2")
        assert await cache.exists("key3")
        assert await cache.exists("key4")

    async def test_get_updates_recency(self):
        cache = SimpleMemoryCache(maxsize=2)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        # Access key1 to make it recently used
        await cache.get("key1")

        # Add third item - should evict key2
        await cache.set("key3", "value3")
        assert await cache.exists("key1")
        assert not await cache.exists("key2")
        assert await cache.exists("key3")

    async def test_add_eviction(self):
        cache = SimpleMemoryCache(maxsize=2)

        await cache.add("key1", "value1")
        await cache.add("key2", "value2")

        # Add third item - should evict key1
        await cache.add("key3", "value3")
        assert not await cache.exists("key1")
        assert await cache.exists("key2")
        assert await cache.exists("key3")

    async def test_multi_set_eviction(self):
        cache = SimpleMemoryCache(maxsize=3)

        # Initial items
        await cache.set("key1", "value1")

        # Add two more items via multi_set
        await cache.multi_set([("key2", "value2"), ("key3", "value3")])

        # Add two more - should evict two oldest items
        await cache.multi_set([("key4", "value4"), ("key5", "value5")])

        assert not await cache.exists("key1")
        assert not await cache.exists("key2")
        assert await cache.exists("key3")  # key3 was most recent before multi_set
        assert await cache.exists("key4")
        assert await cache.exists("key5")

    async def test_no_eviction_when_below_maxsize(self):
        cache = SimpleMemoryCache(maxsize=5)

        for i in range(4):
            await cache.set(f"key{i}", f"value{i}")

        assert len(cache._cache) == 4
        for i in range(4):
            assert await cache.exists(f"key{i}")

    async def test_ttl_doesnt_affect_eviction_order(self):
        cache = SimpleMemoryCache(maxsize=2)

        await cache.set("key1", "value1", ttl=10)
        await cache.set("key2", "value2")

        # Access key1 to make it recently used
        await cache.get("key1")

        # Add third item - should evict key2 despite key1 having TTL
        await cache.set("key3", "value3")
        assert await cache.exists("key1")
        assert not await cache.exists("key2")
        assert await cache.exists("key3")

    async def test_clear_resets_size(self):
        cache = SimpleMemoryCache(maxsize=2)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        assert len(cache._cache) == 2

        await cache.clear()
        assert len(cache._cache) == 0

        # Should be able to add new items without immediate eviction
        await cache.set("key3", "value3")
        await cache.set("key4", "value4")
        assert await cache.exists("key3")
        assert await cache.exists("key4")
        assert len(cache._cache) == 2

    async def test_delete_updates_size(self):
        cache = SimpleMemoryCache(maxsize=2)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        assert len(cache._cache) == 2

        await cache.delete("key1")
        assert len(cache._cache) == 1

        # Should be able to add new item without eviction
        await cache.set("key3", "value3")
        assert await cache.exists("key2")
        assert await cache.exists("key3")
        assert len(cache._cache) == 2

    async def test_increment_updates_recency(self):
        cache = SimpleMemoryCache(maxsize=2)

        await cache.set("key1", 1)
        await cache.set("key2", 2)

        # Increment key1 to make it recently used
        await cache.increment("key1", 1)

        # Add third item - should evict key2
        await cache.set("key3", 3)
        assert await cache.exists("key1")
        assert not await cache.exists("key2")
        assert await cache.exists("key3")
        assert await cache.get("key1") == 2

    async def test_lru_eviction_with_handlers(self):
        cache = SimpleMemoryCache(maxsize=2)

        # Add two items with TTL
        await cache.set("key1", "value1", ttl=10)
        await cache.set("key2", "value2", ttl=10)

        key2_handler = cache._handlers["key2"]

        # Add a third item to trigger eviction
        await cache.set("key3", "value3")

        assert "key1" not in cache._cache
        assert "key1" not in cache._handlers
        assert "key2" in cache._cache
        assert cache._handlers.get("key2") is key2_handler  # Same handler instance
        assert "key3" in cache._cache
        assert "key3" not in cache._handlers  # No TTL

    async def test_custom_serializer(self):
        value = {"one": {"nested": "1"}, "two": 2}
        serialized = pickle.dumps(value)

        # use the main constructor instead of fixture for coverage
        async with SimpleMemoryCache(serializer=PickleSerializer()) as smc:
            assert isinstance(smc.serializer, PickleSerializer)
            await smc.set(Keys.KEY, value)
            assert await smc.get(Keys.KEY) == pickle.loads(serialized)
