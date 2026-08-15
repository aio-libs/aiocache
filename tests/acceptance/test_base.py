import asyncio

import pytest

from aiocache.backends.memory import SimpleMemoryCache
from aiocache.base import _Conn
from aiocache.serializers import NullSerializer
from ..utils import Keys


class TestCache:
    """
    This class ensures that all caches behave the same way and have the minimum functionality.
    To add a new cache just create the fixture for the new cache and add id as a param for the
    cache fixture
    """

    async def test_setup(self, cache):
        assert cache.namespace == "test"

    async def test_get_missing(self, cache):
        assert await cache.get(Keys.KEY) is None
        assert await cache.get(Keys.KEY, default=1) == 1

    async def test_get_existing(self, cache):
        await cache.set(Keys.KEY, "value")
        assert await cache.get(Keys.KEY) == "value"

    async def test_multi_get(self, cache):
        await cache.set(Keys.KEY, "value")
        assert await cache.multi_get([Keys.KEY, Keys.KEY_1]) == ["value", None]

    async def test_delete_missing(self, cache):
        result = await cache.delete(Keys.KEY)
        assert result == 0

    async def test_delete_existing(self, cache):
        await cache.set(Keys.KEY, "value")
        result = await cache.delete(Keys.KEY)
        assert result == 1

        value = await cache.get(Keys.KEY)
        assert value is None

    async def test_set(self, cache):
        assert await cache.set(Keys.KEY, "value") is True

    async def test_set_cancel_previous_ttl_handle(self, cache):
        await cache.set(Keys.KEY, "value", ttl=4)

        await asyncio.sleep(2.1)
        # Smaller ttl seems flaky, as if this call takes >0.5s...
        result = await cache.get(Keys.KEY)
        assert result == "value"
        await cache.set(Keys.KEY, "new_value", ttl=4)

        await asyncio.sleep(2)
        result = await cache.get(Keys.KEY)
        assert result == "new_value"

    async def test_multi_set(self, cache):
        pairs = [(Keys.KEY, "value"), [Keys.KEY_1, "random_value"]]
        assert await cache.multi_set(pairs) is True
        assert await cache.multi_get([Keys.KEY, Keys.KEY_1]) == ["value", "random_value"]

    async def test_multi_set_with_ttl(self, cache):
        pairs = [(Keys.KEY, "value"), [Keys.KEY_1, "random_value"]]
        assert await cache.multi_set(pairs, ttl=1) is True
        await asyncio.sleep(1.1)

        assert await cache.multi_get([Keys.KEY, Keys.KEY_1]) == [None, None]

    async def test_set_with_ttl(self, cache):
        await cache.set(Keys.KEY, "value", ttl=1)
        await asyncio.sleep(1.1)

        assert await cache.get(Keys.KEY) is None

    async def test_add_missing(self, cache):
        assert await cache.add(Keys.KEY, "value", ttl=1) is True

    async def test_add_existing(self, cache):
        assert await cache.set(Keys.KEY, "value") is True
        with pytest.raises(ValueError):
            await cache.add(Keys.KEY, "value")

    async def test_exists_missing(self, cache):
        assert await cache.exists(Keys.KEY) is False

    async def test_exists_existing(self, cache):
        await cache.set(Keys.KEY, "value")
        assert await cache.exists(Keys.KEY) is True

    async def test_increment_missing(self, cache):
        assert await cache.increment(Keys.KEY, delta=2) == 2
        assert await cache.increment(Keys.KEY_1, delta=-2) == -2

    async def test_increment_existing(self, cache):
        await cache.set(Keys.KEY, 2)
        assert await cache.increment(Keys.KEY, delta=2) == 4
        assert await cache.increment(Keys.KEY, delta=1) == 5
        assert await cache.increment(Keys.KEY, delta=-3) == 2

    async def test_increment_typeerror(self, cache):
        await cache.set(Keys.KEY, "value")
        with pytest.raises(TypeError):
            assert await cache.increment(Keys.KEY)

    async def test_expire_existing(self, cache):
        await cache.set(Keys.KEY, "value")
        assert await cache.expire(Keys.KEY, 1) is True
        await asyncio.sleep(1.1)
        assert await cache.exists(Keys.KEY) is False

    async def test_expire_with_0(self, cache):
        await cache.set(Keys.KEY, "value", 1)
        assert await cache.expire(Keys.KEY, 0) is True
        await asyncio.sleep(1.1)
        assert await cache.exists(Keys.KEY) is True

    async def test_expire_missing(self, cache):
        assert await cache.expire(Keys.KEY, 1) is False

    async def test_close_pool_only_clears_resources(self, cache):
        await cache.set(Keys.KEY, "value")
        await cache.close()
        assert await cache.set(Keys.KEY, "value") is True
        assert await cache.get(Keys.KEY) == "value"

    async def test_single_connection(self, cache):
        async with cache.get_connection() as conn:
            assert isinstance(conn, _Conn)
            assert await conn.set(Keys.KEY, "value") is True
            assert await conn.get(Keys.KEY) == "value"


class TestMemoryCache:
    async def test_accept_explicit_args(self):
        with pytest.raises(TypeError):
            SimpleMemoryCache(random_attr="wtf")

    async def test_set_float_ttl(self, memory_cache):
        await memory_cache.set(Keys.KEY, "value", ttl=0.1)
        await asyncio.sleep(0.15)

        assert await memory_cache.get(Keys.KEY) is None

    async def test_multi_set_float_ttl(self, memory_cache):
        pairs = [(Keys.KEY, "value"), [Keys.KEY_1, "random_value"]]
        assert await memory_cache.multi_set(pairs, ttl=0.1) is True
        await asyncio.sleep(0.15)

        assert await memory_cache.multi_get([Keys.KEY, Keys.KEY_1]) == [None, None]

    async def test_raw(self, memory_cache):
        await memory_cache.raw("setdefault", "key", "value")
        assert await memory_cache.raw("get", "key") == "value"
        assert list(await memory_cache.raw("keys")) == ["key"]

    async def test_clear_with_namespace_memory(self, memory_cache):
        await memory_cache.set(Keys.KEY, "value", namespace="test")
        await memory_cache.clear(namespace="test")

        assert await memory_cache.exists(Keys.KEY, namespace="test") is False

    async def test_clear_matches_custom_key_builder_prefix_memory(self):
        """clear() must match the prefix the key_builder makes, not the bare
        namespace, so a builder with its own separator still scopes correctly.
        """
        cache = SimpleMemoryCache(
            namespace="ns", key_builder=lambda k, ns: f"{ns}__{k}" if ns else k
        )
        await cache.set(Keys.KEY, "value")
        await cache.set(Keys.KEY, "other", namespace="nsother")

        await cache.clear()

        assert await cache.exists(Keys.KEY) is False
        assert await cache.exists(Keys.KEY, namespace="nsother") is True

    async def test_clear_rejects_key_builder_without_namespace_memory(self):
        """A builder dropping the namespace makes every key match the prefix,
        so clearing one namespace would empty the whole cache. Refuse instead.
        """
        cache = SimpleMemoryCache(namespace="ns", key_builder=lambda k, ns: k)
        await cache.set(Keys.KEY, "value")

        with pytest.raises(ValueError, match="empty prefix"):
            await cache.clear()

        assert await cache.get(Keys.KEY) == "value"

    async def test_clear_only_removes_own_namespace_memory(self, memory_cache):
        await memory_cache.set(Keys.KEY, "value")
        await memory_cache.set(Keys.KEY, "other", namespace="other")

        await memory_cache.clear()

        assert await memory_cache.exists(Keys.KEY) is False
        assert await memory_cache.exists(Keys.KEY, namespace="other") is True


@pytest.mark.memcached
class TestMemcachedCache:
    async def test_accept_explicit_args(self):
        from aiocache.backends.memcached import MemcachedCache

        with pytest.raises(TypeError):
            MemcachedCache(random_attr="wtf")

    async def test_set_too_long_key(self, memcached_cache):
        with pytest.raises(TypeError) as exc_info:
            await memcached_cache.set("a" * 2000, "value")
        assert str(exc_info.value).startswith("aiomcache error: invalid key")

    async def test_set_float_ttl_fails(self, memcached_cache):
        with pytest.raises(TypeError) as exc_info:
            await memcached_cache.set(Keys.KEY, "value", ttl=0.1)
        assert str(exc_info.value) == "aiomcache error: exptime not int: 0.1"

    async def test_multi_set_float_ttl(self, memcached_cache):
        with pytest.raises(TypeError) as exc_info:
            pairs = [(Keys.KEY, "value"), [Keys.KEY_1, "random_value"]]
            assert await memcached_cache.multi_set(pairs, ttl=0.1) is True
        assert str(exc_info.value) == "aiomcache error: exptime not int: 0.1"

    async def test_raw(self, memcached_cache):
        await memcached_cache.raw("set", b"key", b"value")
        assert await memcached_cache.raw("get", b"key") == "value"
        assert await memcached_cache.raw("prepend", b"key", b"super") is True
        assert await memcached_cache.raw("get", b"key") == "supervalue"

    async def test_clear_with_namespace_memcached(self, memcached_cache):
        await memcached_cache.set(Keys.KEY, "value", namespace="test")

        with pytest.raises(ValueError):
            await memcached_cache.clear(namespace="test")

        assert await memcached_cache.exists(Keys.KEY, namespace="test") is True

    async def test_clear_namespaced_cache_memcached(self, memcached_cache):
        await memcached_cache.set(Keys.KEY, "value")

        with pytest.raises(ValueError):
            await memcached_cache.clear()

        assert await memcached_cache.exists(Keys.KEY) is True

    async def test_clear_empty_namespace_flushes_memcached(self, memcached_cache):
        await memcached_cache.set(Keys.KEY, "value")

        await memcached_cache.clear(namespace="")

        assert await memcached_cache.exists(Keys.KEY) is False

    async def test_close(self, memcached_cache):
        await memcached_cache.set(Keys.KEY, "value")
        await memcached_cache._close()
        assert memcached_cache.client._pool._pool.qsize() == 0


@pytest.mark.valkey
class TestValkeyCache:
    async def test_accept_explicit_args(self):
        from aiocache.backends.valkey import ValkeyCache

        with pytest.raises(TypeError):
            ValkeyCache(random_attr="wtf")

    async def test_float_ttl(self, valkey_cache):
        await valkey_cache.set(Keys.KEY, "value", ttl=0.1)
        await asyncio.sleep(0.15)

        assert await valkey_cache.get(Keys.KEY) is None

    async def test_multi_set_float_ttl(self, valkey_cache):
        pairs = [(Keys.KEY, "value"), [Keys.KEY_1, "random_value"]]
        assert await valkey_cache.multi_set(pairs, ttl=0.1) is True
        await asyncio.sleep(0.15)

        assert await valkey_cache.multi_get([Keys.KEY, Keys.KEY_1]) == [None, None]

    async def test_raw(self, valkey_cache):
        await valkey_cache.raw("set", "key", "value")
        assert await valkey_cache.raw("get", "key") == "value"
        assert await valkey_cache.raw("scan", b"0", "k*") == [b"0", [b"key"]]
        # .raw() doesn't build key with namespace prefix, clear it manually
        await valkey_cache.raw("delete", "key")

    async def test_raw_no_encoding(self, valkey_config):
        from aiocache.backends.valkey import ValkeyCache

        serializer = NullSerializer(encoding=None)
        async with ValkeyCache(valkey_config, namespace="test", serializer=serializer) as cache:
            await cache.set(Keys.KEY, "value")

            assert await cache.raw("get", Keys.KEY) == b"value"

            await cache.delete(Keys.KEY)

    async def test_clear_with_namespace_valkey(self, valkey_cache):
        await valkey_cache.set(Keys.KEY, "value", namespace="test")
        await valkey_cache.clear(namespace="test")

        assert await valkey_cache.exists(Keys.KEY, namespace="test") is False

    async def test_clear_only_removes_own_namespace_valkey(self, valkey_cache):
        await valkey_cache.set(Keys.KEY, "value")
        await valkey_cache.set(Keys.KEY, "other", namespace="other")

        try:
            await valkey_cache.clear()

            assert await valkey_cache.exists(Keys.KEY) is False
            assert await valkey_cache.exists(Keys.KEY, namespace="other") is True
        finally:
            await valkey_cache.delete(Keys.KEY, namespace="other")

    @pytest.mark.parametrize("namespace", ["ten[a]nt", "ten?nt", "ten*"])
    async def test_clear_escapes_glob_in_namespace_valkey(
        self, valkey_config, namespace
    ):
        """A namespace holding glob syntax must not match another namespace.

        Unescaped, "ten[a]nt:*" is a character class matching "tenant:*", so
        clear() deleted the neighbour's keys and left its own in place.
        """
        from aiocache.backends.valkey import ValkeyCache

        async with ValkeyCache(valkey_config, namespace=namespace) as odd:
            async with ValkeyCache(valkey_config, namespace="tenant") as neighbour:
                await odd.set(Keys.KEY, "mine")
                await neighbour.set(Keys.KEY, "theirs")
                try:
                    await odd.clear()

                    assert await odd.exists(Keys.KEY) is False
                    assert await neighbour.get(Keys.KEY) == "theirs"
                finally:
                    await odd.delete(Keys.KEY)
                    await neighbour.delete(Keys.KEY)

    async def test_clear_matches_custom_key_builder_prefix_valkey(
        self, valkey_config
    ):
        """clear() must match the prefix the key_builder makes, not "<ns>:".

        A builder using its own separator writes "ns__key". Assuming the
        default layout looks for "ns:*", matches nothing, deletes nothing and
        still returns True.
        """
        from aiocache.backends.valkey import ValkeyCache

        def key_builder(key, namespace):
            return f"{namespace}__{key}" if namespace else key

        async with ValkeyCache(
            valkey_config, namespace="ns", key_builder=key_builder
        ) as cache:
            await cache.set(Keys.KEY, "value")
            try:
                assert await cache.clear() is True

                assert await cache.exists(Keys.KEY) is False
            finally:
                await cache.delete(Keys.KEY)

    async def test_clear_rejects_key_builder_without_namespace_valkey(
        self, valkey_config
    ):
        """A builder dropping the namespace leaves nothing to scope the scan.

        The pattern would be a bare "*", so clear() would delete every key in
        the database. It has to refuse instead.
        """
        from aiocache.backends.valkey import ValkeyCache

        async with ValkeyCache(
            valkey_config, namespace="ns", key_builder=lambda k, ns: k
        ) as cache:
            await cache.set(Keys.KEY, "value")
            try:
                with pytest.raises(ValueError, match="empty prefix"):
                    await cache.clear()

                assert await cache.get(Keys.KEY) == "value"
            finally:
                await cache.delete(Keys.KEY)

    async def test_clear_removes_keys_beyond_one_scan_batch(self, valkey_cache):
        keys = [f"{Keys.KEY.value}-{i}" for i in range(2000)]
        for start in range(0, len(keys), 200):
            batch = keys[start:start + 200]
            await asyncio.gather(*(valkey_cache.set(k, "value") for k in batch))

        try:
            await valkey_cache.clear()

            assert await valkey_cache.exists(keys[0]) is False
            assert await valkey_cache.exists(keys[-1]) is False
        finally:
            await valkey_cache.clear()

    async def test_close(self, valkey_cache):
        await valkey_cache.set(Keys.KEY, "value")
        await valkey_cache._close()
