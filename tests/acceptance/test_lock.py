import asyncio

import pytest

from aiocache.lock import OptimisticLock, OptimisticLockError, RedLock
from aiocache.serializers import StringSerializer
from ..utils import KEY_LOCK, Keys


@pytest.fixture
def lock(cache):
    return RedLock(cache, Keys.KEY, 20)


def build_key(key, namespace=None):
    return "custom_key"


def build_key_bytes(key, namespace=None):
    return b"custom_key"


@pytest.fixture
def custom_redis_cache(mocker, redis_cache, build_key=build_key):
    mocker.patch.object(redis_cache, "build_key", new=build_key)
    yield redis_cache


@pytest.fixture
def custom_memory_cache(mocker, memory_cache, build_key=build_key):
    mocker.patch.object(memory_cache, "build_key", new=build_key)
    yield memory_cache


@pytest.fixture
def custom_memcached_cache(mocker, memcached_cache, build_key=build_key_bytes):
    mocker.patch.object(memcached_cache, "build_key", new=build_key)
    yield memcached_cache


class TestRedLock:
    async def test_acquire(self, cache, lock):
        cache.serializer = StringSerializer()
        async with lock:
            assert await cache.get(KEY_LOCK) == lock._value

    async def test_release_does_nothing_when_no_lock(self, lock):
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") is None

    async def test_acquire_release(self, cache, lock):
        async with lock:
            pass
        assert await cache.get(KEY_LOCK) is None

    async def test_locking_dogpile(self, mocker, cache):
        mocker.spy(cache, "get")
        mocker.spy(cache, "set")
        mocker.spy(cache, "_add")

        async def dummy():
            res = await cache.get(Keys.KEY)
            assert res is None

            async with RedLock(cache, Keys.KEY, lease=5):
                res = await cache.get(Keys.KEY)
                if res is not None:
                    return
                await asyncio.sleep(0.1)
                await cache.set(Keys.KEY, "value")

        await asyncio.gather(dummy(), dummy(), dummy(), dummy())
        assert cache._add.call_count == 4
        assert cache.get.call_count == 8
        assert cache.set.call_count == 1, cache.set.call_args_list

    async def test_locking_dogpile_lease_expiration(self, cache):
        async def dummy() -> None:
            res = await cache.get(Keys.KEY)
            assert res is None

            # Lease should expire before cache is set, so res is still None.
            async with RedLock(cache, Keys.KEY, lease=1):
                res = await cache.get(Keys.KEY)
                assert res is None
                await asyncio.sleep(1.1)
                await cache.set(Keys.KEY, "value")

        await asyncio.gather(dummy(), dummy(), dummy(), dummy())

    async def test_locking_dogpile_propagates_exceptions(self, cache):
        async def dummy():
            async with RedLock(cache, Keys.KEY, lease=1):
                raise ValueError()

        with pytest.raises(ValueError):
            await dummy()


class TestMemoryRedLock:
    @pytest.fixture
    def lock(self, memory_cache):
        return RedLock(memory_cache, Keys.KEY, 20)

    async def test_acquire_key_builder(self, custom_memory_cache, lock):
        async with lock:
            assert await custom_memory_cache.get(KEY_LOCK) == lock._value

    async def test_acquire_release_key_builder(self, custom_memory_cache, lock):
        async with lock:
            assert await custom_memory_cache.get(KEY_LOCK) is not None
        assert await custom_memory_cache.get(KEY_LOCK) is None

    async def test_release_wrong_token_fails(self, lock):
        await lock.__aenter__()
        lock._value = "random"
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") is None

    async def test_release_wrong_client_fails(self, memory_cache, lock):
        wrong_lock = RedLock(memory_cache, Keys.KEY, 20)
        await lock.__aenter__()
        assert await wrong_lock.__aexit__("exc_type", "exc_value", "traceback") is None

    async def test_float_lease(self, memory_cache):
        lock = RedLock(memory_cache, Keys.KEY, 0.1)
        await lock.__aenter__()
        await asyncio.sleep(0.2)
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") is None


class TestRedisRedLock:
    @pytest.fixture
    def lock(self, redis_cache):
        return RedLock(redis_cache, Keys.KEY, 20)

    async def test_acquire_key_builder(self, custom_redis_cache, lock):
        custom_redis_cache.serializer = StringSerializer()
        async with lock:
            assert await custom_redis_cache.get(KEY_LOCK) == lock._value

    async def test_acquire_release_key_builder(self, custom_redis_cache, lock):
        custom_redis_cache.serializer = StringSerializer()
        async with lock:
            assert await custom_redis_cache.get(KEY_LOCK) is not None
        assert await custom_redis_cache.get(KEY_LOCK) is None

    async def test_release_wrong_token_fails(self, lock):
        await lock.__aenter__()
        lock._value = "random"
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") is None

    async def test_release_wrong_client_fails(self, redis_cache, lock):
        wrong_lock = RedLock(redis_cache, Keys.KEY, 20)
        await lock.__aenter__()
        assert await wrong_lock.__aexit__("exc_type", "exc_value", "traceback") is None

    async def test_float_lease(self, redis_cache):
        lock = RedLock(redis_cache, Keys.KEY, 0.1)
        await lock.__aenter__()
        await asyncio.sleep(0.2)
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") is None


class TestMemcachedRedLock:
    @pytest.fixture
    def lock(self, memcached_cache):
        return RedLock(memcached_cache, Keys.KEY, 20)

    async def test_acquire_key_builder(self, custom_memcached_cache, lock):
        custom_memcached_cache.serializer = StringSerializer()
        async with lock:
            assert await custom_memcached_cache.get(KEY_LOCK) == lock._value

    async def test_acquire_release_key_builder(self, custom_memcached_cache, lock):
        custom_memcached_cache.serializer = StringSerializer()
        async with lock:
            assert await custom_memcached_cache.get(KEY_LOCK) is not None
        assert await custom_memcached_cache.get(KEY_LOCK) is None

    async def test_release_wrong_token_succeeds_meh(self, lock):
        await lock.__aenter__()
        lock._value = "random"
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") is None

    async def test_release_wrong_client_succeeds_meh(self, memcached_cache, lock):
        wrong_lock = RedLock(memcached_cache, Keys.KEY, 20)
        await lock.__aenter__()
        assert await wrong_lock.__aexit__("exc_type", "exc_value", "traceback") is None

    async def test_float_lease(self, memcached_cache):
        lock = RedLock(memcached_cache, Keys.KEY, 0.1)
        with pytest.raises(TypeError):
            await lock.__aenter__()


class TestOptimisticLock:
    @pytest.fixture
    def lock(self, cache):
        return OptimisticLock(cache, Keys.KEY)

    async def test_acquire(self, cache, lock):
        await cache.set(Keys.KEY, "value")
        async with lock:
            assert lock._token == await cache._gets(cache._build_key(Keys.KEY))

    async def test_release_does_nothing(self, lock):
        assert await lock.__aexit__("exc_type", "exc_value", "traceback") is None

    async def test_check_and_set_not_existing_never_fails(self, cache, lock):
        async with lock as locked:
            await cache.set(Keys.KEY, "conflicting_value")
            await locked.cas("value")

        assert await cache.get(Keys.KEY) == "value"

    async def test_check_and_set(self, cache, lock):
        await cache.set(Keys.KEY, "previous_value")
        async with lock as locked:
            await locked.cas("value")

        assert await cache.get(Keys.KEY) == "value"

    async def test_check_and_set_fail(self, cache, lock):
        await cache.set(Keys.KEY, "previous_value")
        with pytest.raises(OptimisticLockError):
            async with lock as locked:
                await cache.set(Keys.KEY, "conflicting_value")
                await locked.cas("value")

    async def test_check_and_set_with_int_ttl(self, cache, lock):
        await cache.set(Keys.KEY, "previous_value")
        async with lock as locked:
            await locked.cas("value", ttl=1)

        await asyncio.sleep(1)
        assert await cache.get(Keys.KEY) is None


class TestMemoryOptimisticLock:
    @pytest.fixture
    def lock(self, memory_cache):
        return OptimisticLock(memory_cache, Keys.KEY)

    async def test_acquire_key_builder(self, custom_memory_cache, lock):
        await custom_memory_cache.set(Keys.KEY, "value")
        async with lock:
            assert await custom_memory_cache.get(KEY_LOCK) == lock._token
        await custom_memory_cache.delete(Keys.KEY, "value")

    async def test_check_and_set_with_float_ttl(self, memory_cache, lock):
        await memory_cache.set(Keys.KEY, "previous_value")
        async with lock as locked:
            await locked.cas("value", ttl=0.1)

        await asyncio.sleep(1)
        assert await memory_cache.get(Keys.KEY) is None


class TestRedisOptimisticLock:
    @pytest.fixture
    def lock(self, redis_cache):
        return OptimisticLock(redis_cache, Keys.KEY)

    async def test_acquire_key_builder(self, custom_redis_cache, lock):
        custom_redis_cache.serializer = StringSerializer()
        await custom_redis_cache.set(Keys.KEY, "value")
        async with lock:
            assert await custom_redis_cache.get(KEY_LOCK) == lock._token
        await custom_redis_cache.delete(Keys.KEY, "value")

    async def test_check_and_set_with_float_ttl(self, redis_cache, lock):
        await redis_cache.set(Keys.KEY, "previous_value")
        async with lock as locked:
            await locked.cas("value", ttl=0.1)

        await asyncio.sleep(1)
        assert await redis_cache.get(Keys.KEY) is None
