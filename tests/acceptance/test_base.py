import asyncio

import pytest

from aiocache.backends.memcached import MemcachedCache
from aiocache.backends.memory import SimpleMemoryCache
from aiocache.backends.redis import RedisCache
from aiocache.base import _Conn


class TestCache:
    """
    This class ensures that all caches behave the same way and have the minimum functionality.
    To add a new cache just create the fixture for the new cache and add id as a param for the
    cache fixture
    """

    @pytest.mark.asyncio
    async def test_setup(self, cache):
        assert cache.namespace == "test"

    @pytest.mark.asyncio
    async def test_get_missing(self, cache):
        assert await cache.get(pytest.KEY) is None
        assert await cache.get(pytest.KEY, default=1) == 1

    @pytest.mark.asyncio
    async def test_get_existing(self, cache):
        await cache.set(pytest.KEY, "value")
        assert await cache.get(pytest.KEY) == "value"

    @pytest.mark.asyncio
    async def test_multi_get(self, cache):
        await cache.set(pytest.KEY, "value")
        assert await cache.multi_get([pytest.KEY, pytest.KEY_1]) == ["value", None]

    @pytest.mark.asyncio
    async def test_delete_missing(self, cache):
        assert await cache.delete(pytest.KEY) == 0

    @pytest.mark.asyncio
    async def test_delete_existing(self, cache):
        await cache.set(pytest.KEY, "value")
        assert await cache.delete(pytest.KEY) == 1

        assert await cache.get(pytest.KEY) is None

    @pytest.mark.asyncio
    async def test_set(self, cache):
        assert await cache.set(pytest.KEY, "value") is True

    @pytest.mark.asyncio
    async def test_set_cancel_previous_ttl_handle(self, cache):
        await cache.set(pytest.KEY, "value", ttl=2)

        await asyncio.sleep(1)
        assert await cache.get(pytest.KEY) == "value"
        await cache.set(pytest.KEY, "new_value", ttl=2)

        await asyncio.sleep(1)
        assert await cache.get(pytest.KEY) == "new_value"

    @pytest.mark.asyncio
    async def test_multi_set(self, cache):
        pairs = [(pytest.KEY, "value"), [pytest.KEY_1, "random_value"]]
        assert await cache.multi_set(pairs) is True
        assert await cache.multi_get([pytest.KEY, pytest.KEY_1]) == ["value", "random_value"]

    @pytest.mark.asyncio
    async def test_multi_set_with_ttl(self, cache):
        pairs = [(pytest.KEY, "value"), [pytest.KEY_1, "random_value"]]
        assert await cache.multi_set(pairs, ttl=1) is True
        await asyncio.sleep(1.1)

        assert await cache.multi_get([pytest.KEY, pytest.KEY_1]) == [None, None]

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache):
        await cache.set(pytest.KEY, "value", ttl=1)
        await asyncio.sleep(1.1)

        assert await cache.get(pytest.KEY) is None

    @pytest.mark.asyncio
    async def test_add_missing(self, cache):
        assert await cache.add(pytest.KEY, "value", ttl=1) is True

    @pytest.mark.asyncio
    async def test_add_existing(self, cache):
        assert await cache.set(pytest.KEY, "value") is True
        with pytest.raises(ValueError):
            await cache.add(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_exists_missing(self, cache):
        assert await cache.exists(pytest.KEY) is False

    @pytest.mark.asyncio
    async def test_exists_existing(self, cache):
        await cache.set(pytest.KEY, "value")
        assert await cache.exists(pytest.KEY) is True

    @pytest.mark.asyncio
    async def test_increment_missing(self, cache):
        assert await cache.increment(pytest.KEY, delta=2) == 2
        assert await cache.increment(pytest.KEY_1, delta=-2) == -2

    @pytest.mark.asyncio
    async def test_increment_existing(self, cache):
        await cache.set(pytest.KEY, 2)
        assert await cache.increment(pytest.KEY, delta=2) == 4
        assert await cache.increment(pytest.KEY, delta=1) == 5
        assert await cache.increment(pytest.KEY, delta=-3) == 2

    @pytest.mark.asyncio
    async def test_increment_typeerror(self, cache):
        await cache.set(pytest.KEY, "value")
        with pytest.raises(TypeError):
            assert await cache.increment(pytest.KEY)

    @pytest.mark.asyncio
    async def test_expire_existing(self, cache):
        await cache.set(pytest.KEY, "value")
        assert await cache.expire(pytest.KEY, 1) is True
        await asyncio.sleep(1.1)
        assert await cache.exists(pytest.KEY) is False

    @pytest.mark.asyncio
    async def test_expire_with_0(self, cache):
        await cache.set(pytest.KEY, "value", 1)
        assert await cache.expire(pytest.KEY, 0) is True
        await asyncio.sleep(1.1)
        assert await cache.exists(pytest.KEY) is True

    @pytest.mark.asyncio
    async def test_expire_missing(self, cache):
        assert await cache.expire(pytest.KEY, 1) is False

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        await cache.set(pytest.KEY, "value")
        await cache.clear()

        assert await cache.exists(pytest.KEY) is False

    @pytest.mark.asyncio
    async def test_close_pool_only_clears_resources(self, cache):
        await cache.set(pytest.KEY, "value")
        await cache.close()
        assert await cache.set(pytest.KEY, "value") is True
        assert await cache.get(pytest.KEY) == "value"

    @pytest.mark.asyncio
    async def test_single_connection(self, cache):
        pytest.skip("aioredis code is broken")
        async with cache.get_connection() as conn:
            assert isinstance(conn, _Conn)
            assert await conn.set(pytest.KEY, "value") is True
            assert await conn.get(pytest.KEY) == "value"


class TestMemoryCache:
    @pytest.mark.asyncio
    async def test_accept_explicit_args(self):
        with pytest.raises(TypeError):
            SimpleMemoryCache(random_attr="wtf")

    @pytest.mark.asyncio
    async def test_set_float_ttl(self, memory_cache):
        await memory_cache.set(pytest.KEY, "value", ttl=0.1)
        await asyncio.sleep(0.15)

        assert await memory_cache.get(pytest.KEY) is None

    @pytest.mark.asyncio
    async def test_multi_set_float_ttl(self, memory_cache):
        pairs = [(pytest.KEY, "value"), [pytest.KEY_1, "random_value"]]
        assert await memory_cache.multi_set(pairs, ttl=0.1) is True
        await asyncio.sleep(0.15)

        assert await memory_cache.multi_get([pytest.KEY, pytest.KEY_1]) == [None, None]

    @pytest.mark.asyncio
    async def test_raw(self, memory_cache):
        await memory_cache.raw("setdefault", "key", "value")
        assert await memory_cache.raw("get", "key") == "value"
        assert list(await memory_cache.raw("keys")) == ["key"]

    @pytest.mark.asyncio
    async def test_clear_with_namespace_memory(self, memory_cache):
        await memory_cache.set(pytest.KEY, "value", namespace="test")
        await memory_cache.clear(namespace="test")

        assert await memory_cache.exists(pytest.KEY, namespace="test") is False


class TestMemcachedCache:
    @pytest.mark.asyncio
    async def test_accept_explicit_args(self):
        with pytest.raises(TypeError):
            MemcachedCache(random_attr="wtf")

    @pytest.mark.asyncio
    async def test_set_too_long_key(self, memcached_cache):
        with pytest.raises(TypeError) as exc_info:
            await memcached_cache.set("a" * 2000, "value")
        assert str(exc_info.value).startswith("aiomcache error: invalid key")

    @pytest.mark.asyncio
    async def test_set_float_ttl_fails(self, memcached_cache):
        with pytest.raises(TypeError) as exc_info:
            await memcached_cache.set(pytest.KEY, "value", ttl=0.1)
        assert str(exc_info.value) == "aiomcache error: exptime not int: 0.1"

    @pytest.mark.asyncio
    async def test_multi_set_float_ttl(self, memcached_cache):
        with pytest.raises(TypeError) as exc_info:
            pairs = [(pytest.KEY, "value"), [pytest.KEY_1, "random_value"]]
            assert await memcached_cache.multi_set(pairs, ttl=0.1) is True
        assert str(exc_info.value) == "aiomcache error: exptime not int: 0.1"

    @pytest.mark.asyncio
    async def test_raw(self, memcached_cache):
        await memcached_cache.raw("set", b"key", b"value")
        assert await memcached_cache.raw("get", b"key") == "value"
        assert await memcached_cache.raw("prepend", b"key", b"super") is True
        assert await memcached_cache.raw("get", b"key") == "supervalue"

    @pytest.mark.asyncio
    async def test_clear_with_namespace_memcached(self, memcached_cache):
        await memcached_cache.set(pytest.KEY, "value", namespace="test")

        with pytest.raises(ValueError):
            await memcached_cache.clear(namespace="test")

        assert await memcached_cache.exists(pytest.KEY, namespace="test") is True

    @pytest.mark.asyncio
    async def test_close(self, memcached_cache):
        await memcached_cache.set(pytest.KEY, "value")
        await memcached_cache._close()
        assert memcached_cache.client._pool._pool.qsize() == 0


class TestRedisCache:
    @pytest.mark.asyncio
    async def test_accept_explicit_args(self):
        with pytest.raises(TypeError):
            RedisCache(random_attr="wtf")

    @pytest.mark.asyncio
    async def test_float_ttl(self, redis_cache):
        await redis_cache.set(pytest.KEY, "value", ttl=0.1)
        await asyncio.sleep(0.15)

        assert await redis_cache.get(pytest.KEY) is None

    @pytest.mark.asyncio
    async def test_multi_set_float_ttl(self, redis_cache):
        pairs = [(pytest.KEY, "value"), [pytest.KEY_1, "random_value"]]
        assert await redis_cache.multi_set(pairs, ttl=0.1) is True
        await asyncio.sleep(0.15)

        assert await redis_cache.multi_get([pytest.KEY, pytest.KEY_1]) == [None, None]

    @pytest.mark.asyncio
    async def test_raw(self, redis_cache):
        await redis_cache.raw("set", "key", "value")
        assert await redis_cache.raw("get", "key") == "value"
        assert await redis_cache.raw("keys", "k*") == ["key"]

    @pytest.mark.asyncio
    async def test_clear_with_namespace_redis(self, redis_cache):
        await redis_cache.set(pytest.KEY, "value", namespace="test")
        await redis_cache.clear(namespace="test")

        assert await redis_cache.exists(pytest.KEY, namespace="test") is False

    @pytest.mark.asyncio
    async def test_close(self, redis_cache):
        await redis_cache.set(pytest.KEY, "value")
        await redis_cache._close()
        assert redis_cache._pool.size == 0
