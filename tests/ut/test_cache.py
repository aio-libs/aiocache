import pytest
import asyncio
import asynctest
import aiocache

from aiocache import SimpleMemoryCache, MemcachedCache
from aiocache.cache import BaseCache


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
    @pytest.mark.asyncio
    async def test_get(self, mock_cache):
        await mock_cache.get(pytest.KEY)

        assert mock_cache.serializer.loads.call_count == 1
        assert mock_cache._build_key.call_count == 1
        assert mock_cache.plugins[0].pre_get.call_count == 1
        assert mock_cache.plugins[0].post_get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_timeouts(self, mock_cache):
        mock_cache._get = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

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
        mock_cache._set = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

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
        mock_cache._add = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

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
        mock_cache._multi_get = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

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
        mock_cache._multi_set = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.multi_set([[pytest.KEY, "value"], [pytest.KEY_1, "value1"]])

    @pytest.mark.asyncio
    async def test_exists(self, mock_cache):
        await mock_cache.exists(pytest.KEY)

        assert mock_cache._build_key.call_count == 1

    @pytest.mark.asyncio
    async def test_exists_timeouts(self, mock_cache):
        mock_cache._exists = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.exists(pytest.KEY)

    @pytest.mark.asyncio
    async def test_delete(self, mock_cache):
        await mock_cache.delete(pytest.KEY)

        assert mock_cache._build_key.call_count == 1

    @pytest.mark.asyncio
    async def test_delete_timeouts(self, mock_cache):
        mock_cache._delete = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.delete(pytest.KEY)

    @pytest.mark.asyncio
    async def test_expire(self, mock_cache):
        await mock_cache.expire(pytest.KEY, 1)
        mock_cache._expire.assert_called_with(mock_cache._build_key(pytest.KEY), 1)

    @pytest.mark.asyncio
    async def test_expire_timeouts(self, mock_cache):
        mock_cache._expire = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.expire(pytest.KEY, 0)

    @pytest.mark.asyncio
    async def test_clear(self, mock_cache):
        await mock_cache.clear(pytest.KEY)
        mock_cache._clear.assert_called_with(mock_cache._build_key(pytest.KEY))

    @pytest.mark.asyncio
    async def test_clear_timeouts(self, mock_cache):
        mock_cache._clear = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.clear(pytest.KEY)

    @pytest.mark.asyncio
    async def test_raw(self, mock_cache):
        await mock_cache.raw("get", pytest.KEY)
        mock_cache._raw.assert_called_with("get", mock_cache._build_key(pytest.KEY))

    @pytest.mark.asyncio
    async def test_raw_timeouts(self, mock_cache):
        mock_cache._raw = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

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
    def test_build_key(self, set_test_namespace, mock_cache, namespace, expected):
        assert mock_cache._build_key(pytest.KEY, namespace=namespace) == expected


class TestRedisCache:
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
