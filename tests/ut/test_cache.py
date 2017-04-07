import os
import pytest
import asyncio
import asynctest
import aiocache

from unittest.mock import patch, MagicMock, ANY

from aiocache import SimpleMemoryCache, MemcachedCache
from aiocache.cache import BaseCache, API


class TestAPI:

    def test_register(self):
        @API.register
        def dummy():
            pass

        assert dummy in API.CMDS
        API.unregister(dummy)

    def test_unregister(self):
        @API.register
        def dummy():
            pass

        API.unregister(dummy)
        assert dummy not in API.CMDS

    def test_unregister_unexisting(self):
        def dummy():
            pass

        API.unregister(dummy)
        assert dummy not in API.CMDS

    @pytest.mark.asyncio
    async def test_aiocache_enabled(self):
        @API.aiocache_enabled()
        async def dummy(*args, **kwargs):
            return True

        assert await dummy() is True

    @pytest.mark.asyncio
    async def test_aiocache_enabled_disabled(self):
        @API.aiocache_enabled(fake_return=[])
        async def dummy(*args, **kwargs):
            return True

        with patch.dict(os.environ, {'AIOCACHE_DISABLE': '1'}):
            assert await dummy() == []

    @pytest.mark.asyncio
    async def test_timeout_no_timeout(self):
        self = MagicMock()
        self.timeout = 0

        @API.timeout
        async def dummy(self):
            self()

        with patch("asyncio.wait_for") as wait_for:
            await dummy(self)
            assert self.call_count == 1
            assert wait_for.call_count == 0

    @pytest.mark.asyncio
    async def test_timeout_self(self):
        self = MagicMock()
        self.timeout = 0.002

        @API.timeout
        async def dummy(self):
            await asyncio.sleep(0.005)

        with pytest.raises(asyncio.TimeoutError):
            await dummy(self)

    @pytest.mark.asyncio
    async def test_timeout_kwarg(self):
        self = MagicMock()

        @API.timeout
        async def dummy(self):
            await asyncio.sleep(0.005)

        with pytest.raises(asyncio.TimeoutError):
            await dummy(self, timeout=0.002)

    @pytest.mark.asyncio
    async def test_timeout_self_kwarg(self):
        self = MagicMock()
        self.timeout = 5

        @API.timeout
        async def dummy(self):
            await asyncio.sleep(0.005)

        with pytest.raises(asyncio.TimeoutError):
            await dummy(self, timeout=0.003)

    @pytest.mark.asyncio
    async def test_plugins(self):
        self = MagicMock()
        plugin1 = asynctest.CoroutineMock()
        plugin2 = asynctest.CoroutineMock()
        self.plugins = [plugin1, plugin2]

        @API.plugins
        async def dummy(self, *args, **kwargs):
            return True

        assert await dummy(self) is True
        plugin1.pre_dummy.assert_called_with(self)
        plugin1.post_dummy.assert_called_with(self, took=ANY, ret=True)


class TestBaseCache:
    """
    Tests that the client calls do nothing. If a BaseCache is instantiated, it must not interact
    with the underlying storage.
    """
    @pytest.mark.asyncio
    async def test_add(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._add(pytest.KEY, "value", 0)

    @pytest.mark.asyncio
    async def test_get(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._get(pytest.KEY)

    @pytest.mark.asyncio
    async def test_set(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._set(pytest.KEY, "value", 0)

    @pytest.mark.asyncio
    async def test_multi_get(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._multi_get([pytest.KEY])

    @pytest.mark.asyncio
    async def test_multi_set(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._multi_set([(pytest.KEY, "value")], 0)

    @pytest.mark.asyncio
    async def test_delete(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._delete(pytest.KEY)

    @pytest.mark.asyncio
    async def test_exists(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._exists(pytest.KEY)

    @pytest.mark.asyncio
    async def test_expire(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._expire(pytest.KEY, 0)

    @pytest.mark.asyncio
    async def test_clear(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._clear("namespace")

    @pytest.mark.asyncio
    async def test_raw(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._raw("get", pytest.KEY)


class TestCache:
    """
    This class ensures that all backends behave the same way at logic level. It tries to ensure
    the calls to the necessary methods like serialization and strategies are performed when needed.
    To add a new backend just create the fixture for the new backend and add id as a param for the
    cache fixture.

    The calls to the client are mocked so it doesn't interact with any storage.
    """
    async def asleep(self, *args, **kwargs):
        await asyncio.sleep(0.005)

    @pytest.mark.asyncio
    async def test_get(self, mock_cache):
        await mock_cache.get(pytest.KEY)

        assert mock_cache.serializer.loads.call_count == 1
        assert mock_cache._build_key.call_count == 1
        assert mock_cache.plugins[0].pre_get.call_count == 1
        assert mock_cache.plugins[0].post_get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_timeouts(self, mock_cache):
        mock_cache._get = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.get(pytest.KEY)

    @pytest.mark.asyncio
    async def test_set(self, mock_cache):
        await mock_cache.set(pytest.KEY, "value")

        assert mock_cache.serializer.dumps.call_count == 1
        assert mock_cache._build_key.call_count == 1
        assert mock_cache.plugins[0].pre_set.call_count == 1
        assert mock_cache.plugins[0].post_set.call_count == 1

    @pytest.mark.asyncio
    async def test_set_timeouts(self, mock_cache):
        mock_cache._set = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.set(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_add(self, mock_cache):
        mock_cache._exists.return_value = False
        await mock_cache.add(pytest.KEY, "value")

        assert mock_cache.serializer.dumps.call_count == 1
        assert mock_cache._build_key.call_count == 1
        assert mock_cache.plugins[0].pre_add.call_count == 1
        assert mock_cache.plugins[0].post_add.call_count == 1

    @pytest.mark.asyncio
    async def test_add_timeouts(self, mock_cache):
        mock_cache._add = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.add(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_mget(self, mock_cache):
        await mock_cache.multi_get([pytest.KEY, pytest.KEY_1])

        assert mock_cache.serializer.loads.call_count == 2
        assert mock_cache._build_key.call_count == 2
        assert mock_cache.plugins[0].pre_multi_get.call_count == 1
        assert mock_cache.plugins[0].post_multi_get.call_count == 1

    @pytest.mark.asyncio
    async def test_mget_timeouts(self, mock_cache):
        mock_cache._multi_get = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.multi_get(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_mset(self, mock_cache):
        await mock_cache.multi_set([[pytest.KEY, "value"], [pytest.KEY_1, "value1"]])

        assert mock_cache.serializer.dumps.call_count == 2
        assert mock_cache._build_key.call_count == 2
        assert mock_cache.plugins[0].pre_multi_set.call_count == 1
        assert mock_cache.plugins[0].post_multi_set.call_count == 1

    @pytest.mark.asyncio
    async def test_mset_timeouts(self, mock_cache):
        mock_cache._multi_set = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.multi_set([[pytest.KEY, "value"], [pytest.KEY_1, "value1"]])

    @pytest.mark.asyncio
    async def test_exists(self, mock_cache):
        await mock_cache.exists(pytest.KEY)

        assert mock_cache._build_key.call_count == 1

    @pytest.mark.asyncio
    async def test_exists_timeouts(self, mock_cache):
        mock_cache._exists = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.exists(pytest.KEY)

    @pytest.mark.asyncio
    async def test_delete(self, mock_cache):
        await mock_cache.delete(pytest.KEY)

        assert mock_cache._build_key.call_count == 1

    @pytest.mark.asyncio
    async def test_delete_timeouts(self, mock_cache):
        mock_cache._delete = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.delete(pytest.KEY)

    @pytest.mark.asyncio
    async def test_expire(self, mock_cache):
        await mock_cache.expire(pytest.KEY, 1)
        mock_cache._expire.assert_called_with(mock_cache._build_key(pytest.KEY), 1)

    @pytest.mark.asyncio
    async def test_expire_timeouts(self, mock_cache):
        mock_cache._expire = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.expire(pytest.KEY, 0)

    @pytest.mark.asyncio
    async def test_clear(self, mock_cache):
        await mock_cache.clear(pytest.KEY)
        mock_cache._clear.assert_called_with(mock_cache._build_key(pytest.KEY))

    @pytest.mark.asyncio
    async def test_clear_timeouts(self, mock_cache):
        mock_cache._clear = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.clear(pytest.KEY)

    @pytest.mark.asyncio
    async def test_raw(self, mock_cache):
        await mock_cache.raw("get", pytest.KEY)
        mock_cache._raw.assert_called_with("get", mock_cache._build_key(pytest.KEY))

    @pytest.mark.asyncio
    async def test_raw_timeouts(self, mock_cache):
        mock_cache._raw = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.raw("clear")

    @pytest.fixture
    def set_test_namespace(self):
        aiocache.settings.DEFAULT_CACHE_KWARGS = {"namespace": "test"}

    @pytest.mark.parametrize("namespace, expected", (
        [None, "test" + pytest.KEY],
        ["", pytest.KEY],
        ["my_ns", "my_ns" + pytest.KEY],)
    )
    def test_build_key(self, set_test_namespace, base_cache, namespace, expected):
        assert base_cache._build_key(pytest.KEY, namespace=namespace) == expected


class TestRedisCache:

    @pytest.fixture(autouse=True)
    def redis_defaults(self):
        aiocache.settings.set_defaults(class_="aiocache.RedisCache")
        yield
        aiocache.settings.set_defaults(class_="aiocache.SimpleMemoryCache")

    @pytest.mark.parametrize("namespace, expected", (
        [None, "test:" + pytest.KEY],
        ["", pytest.KEY],
        ["my_ns", "my_ns:" + pytest.KEY],)
    )
    def test_build_key_double_dot(self, set_test_namespace, redis_cache, namespace, expected):
        assert redis_cache._build_key(pytest.KEY, namespace=namespace) == expected

    def test_build_key_no_namespace(self, redis_cache):
        assert redis_cache._build_key(pytest.KEY, namespace=None) == pytest.KEY


class TestSimpleMemoryCache:

    def test_inheritance(self):
        assert isinstance(SimpleMemoryCache(), BaseCache)


class TestMemcachedCache:

    @pytest.fixture(autouse=True)
    def memcached_defaults(self):
        aiocache.settings.set_defaults(class_="aiocache.MemcachedCache")
        yield
        aiocache.settings.set_defaults(class_="aiocache.MemcachedCache")

    def test_inheritance(self):
        assert isinstance(MemcachedCache(), BaseCache)

    @pytest.mark.parametrize("namespace, expected", (
        [None, "test" + pytest.KEY],
        ["", pytest.KEY],
        ["my_ns", "my_ns" + pytest.KEY],)
    )
    def test_build_key_bytes(self, set_test_namespace, memcached_cache, namespace, expected):
        assert memcached_cache._build_key(pytest.KEY, namespace=namespace) == expected.encode()

    def test_build_key_no_namespace(self, memcached_cache):
        assert memcached_cache._build_key(pytest.KEY, namespace=None) == pytest.KEY.encode()


@pytest.fixture
def set_test_namespace():
    aiocache.settings.DEFAULT_CACHE_KWARGS = {"namespace": "test"}
