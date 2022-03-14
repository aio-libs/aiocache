import asyncio
import os
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from aiocache.base import API, BaseCache, _Conn


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

        with patch.dict(os.environ, {"AIOCACHE_DISABLE": "1"}):
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
    async def test_timeout_kwarg_0(self):
        self = MagicMock()
        self.timeout = 0.002

        @API.timeout
        async def dummy(self):
            await asyncio.sleep(0.005)
            return True

        assert await dummy(self, timeout=0) is True

    @pytest.mark.asyncio
    async def test_timeout_kwarg_None(self):
        self = MagicMock()
        self.timeout = 0.002

        @API.timeout
        async def dummy(self):
            await asyncio.sleep(0.005)
            return True

        assert await dummy(self, timeout=None) is True

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
        plugin1 = MagicMock()
        plugin1.pre_dummy = AsyncMock()
        plugin1.post_dummy = AsyncMock()
        plugin2 = MagicMock()
        plugin2.pre_dummy = AsyncMock()
        plugin2.post_dummy = AsyncMock()
        self.plugins = [plugin1, plugin2]

        @API.plugins
        async def dummy(self, *args, **kwargs):
            return True

        assert await dummy(self) is True
        plugin1.pre_dummy.assert_called_with(self)
        plugin1.post_dummy.assert_called_with(self, took=ANY, ret=True)
        plugin2.pre_dummy.assert_called_with(self)
        plugin2.post_dummy.assert_called_with(self, took=ANY, ret=True)


class TestBaseCache:
    def test_str_ttl(self):
        cache = BaseCache(ttl="1.5")
        assert cache.ttl == 1.5

    def test_str_timeout(self):
        cache = BaseCache(timeout="1.5")
        assert cache.timeout == 1.5

    @pytest.mark.asyncio
    async def test_add(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._add(pytest.KEY, "value", 0)

    @pytest.mark.asyncio
    async def test_get(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._get(pytest.KEY, "utf-8")

    @pytest.mark.asyncio
    async def test_set(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._set(pytest.KEY, "value", 0)

    @pytest.mark.asyncio
    async def test_multi_get(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._multi_get([pytest.KEY], encoding="utf-8")

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
    async def test_increment(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._increment(pytest.KEY, 2)

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

    @pytest.mark.asyncio
    async def test_close(self, base_cache):
        assert await base_cache._close() is None

    @pytest.mark.asyncio
    async def test_acquire_conn(self, base_cache):
        assert await base_cache.acquire_conn() == base_cache

    @pytest.mark.asyncio
    async def test_release_conn(self, base_cache):
        assert await base_cache.release_conn("mock") is None

    @pytest.fixture
    def set_test_namespace(self, base_cache):
        base_cache.namespace = "test"
        yield
        base_cache.namespace = None

    @pytest.mark.parametrize(
        "namespace, expected",
        ([None, "test" + pytest.KEY], ["", pytest.KEY], ["my_ns", "my_ns" + pytest.KEY]),  # type: ignore[attr-defined]  # noqa: B950
    )
    def test_build_key(self, set_test_namespace, base_cache, namespace, expected):
        assert base_cache.build_key(pytest.KEY, namespace=namespace) == expected

    def test_alt_build_key(self):
        cache = BaseCache(key_builder=lambda key, namespace: "x")
        assert cache.build_key(pytest.KEY, "namespace") == "x"

    @pytest.mark.asyncio
    async def test_add_ttl_cache_default(self, base_cache):
        base_cache._add = AsyncMock()

        await base_cache.add(pytest.KEY, "value")

        base_cache._add.assert_called_once_with(pytest.KEY, "value", _conn=None, ttl=None)

    @pytest.mark.asyncio
    async def test_add_ttl_default(self, base_cache):
        base_cache.ttl = 10
        base_cache._add = AsyncMock()

        await base_cache.add(pytest.KEY, "value")

        base_cache._add.assert_called_once_with(pytest.KEY, "value", _conn=None, ttl=10)

    @pytest.mark.asyncio
    async def test_add_ttl_overriden(self, base_cache):
        base_cache.ttl = 10
        base_cache._add = AsyncMock()

        await base_cache.add(pytest.KEY, "value", ttl=20)

        base_cache._add.assert_called_once_with(pytest.KEY, "value", _conn=None, ttl=20)

    @pytest.mark.asyncio
    async def test_add_ttl_none(self, base_cache):
        base_cache.ttl = 10
        base_cache._add = AsyncMock()

        await base_cache.add(pytest.KEY, "value", ttl=None)

        base_cache._add.assert_called_once_with(pytest.KEY, "value", _conn=None, ttl=None)

    @pytest.mark.asyncio
    async def test_set_ttl_cache_default(self, base_cache):
        base_cache._set = AsyncMock()

        await base_cache.set(pytest.KEY, "value")

        base_cache._set.assert_called_once_with(
            pytest.KEY, "value", _cas_token=None, _conn=None, ttl=None
        )

    @pytest.mark.asyncio
    async def test_set_ttl_default(self, base_cache):
        base_cache.ttl = 10
        base_cache._set = AsyncMock()

        await base_cache.set(pytest.KEY, "value")

        base_cache._set.assert_called_once_with(
            pytest.KEY, "value", _cas_token=None, _conn=None, ttl=10
        )

    @pytest.mark.asyncio
    async def test_set_ttl_overriden(self, base_cache):
        base_cache.ttl = 10
        base_cache._set = AsyncMock()

        await base_cache.set(pytest.KEY, "value", ttl=20)

        base_cache._set.assert_called_once_with(
            pytest.KEY, "value", _cas_token=None, _conn=None, ttl=20
        )

    @pytest.mark.asyncio
    async def test_set_ttl_none(self, base_cache):
        base_cache.ttl = 10
        base_cache._set = AsyncMock()

        await base_cache.set(pytest.KEY, "value", ttl=None)

        base_cache._set.assert_called_once_with(
            pytest.KEY, "value", _cas_token=None, _conn=None, ttl=None
        )

    @pytest.mark.asyncio
    async def test_multi_set_ttl_cache_default(self, base_cache):
        base_cache._multi_set = AsyncMock()

        await base_cache.multi_set([[pytest.KEY, "value"], [pytest.KEY_1, "value1"]])

        base_cache._multi_set.assert_called_once_with(
            [(pytest.KEY, "value"), (pytest.KEY_1, "value1")], _conn=None, ttl=None
        )

    @pytest.mark.asyncio
    async def test_multi_set_ttl_default(self, base_cache):
        base_cache.ttl = 10
        base_cache._multi_set = AsyncMock()

        await base_cache.multi_set([[pytest.KEY, "value"], [pytest.KEY_1, "value1"]])

        base_cache._multi_set.assert_called_once_with(
            [(pytest.KEY, "value"), (pytest.KEY_1, "value1")], _conn=None, ttl=10
        )

    @pytest.mark.asyncio
    async def test_multi_set_ttl_overriden(self, base_cache):
        base_cache.ttl = 10
        base_cache._multi_set = AsyncMock()

        await base_cache.multi_set([[pytest.KEY, "value"], [pytest.KEY_1, "value1"]], ttl=20)

        base_cache._multi_set.assert_called_once_with(
            [(pytest.KEY, "value"), (pytest.KEY_1, "value1")], _conn=None, ttl=20
        )

    @pytest.mark.asyncio
    async def test_multi_set_ttl_none(self, base_cache):
        base_cache.ttl = 10
        base_cache._multi_set = AsyncMock()

        await base_cache.multi_set([[pytest.KEY, "value"], [pytest.KEY_1, "value1"]], ttl=None)

        base_cache._multi_set.assert_called_once_with(
            [(pytest.KEY, "value"), (pytest.KEY_1, "value1")], _conn=None, ttl=None
        )


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

        mock_cache._get.assert_called_with(
            mock_cache._build_key(pytest.KEY), encoding=ANY, _conn=ANY
        )
        assert mock_cache.plugins[0].pre_get.call_count == 1
        assert mock_cache.plugins[0].post_get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_timeouts(self, mock_cache):
        mock_cache._get = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.get(pytest.KEY)

    @pytest.mark.asyncio
    async def test_get_default(self, mock_cache):
        mock_cache._serializer.loads.return_value = None

        assert await mock_cache.get(pytest.KEY, default=1) == 1

    @pytest.mark.asyncio
    async def test_get_negative_default(self, mock_cache):
        mock_cache._serializer.loads.return_value = False

        assert await mock_cache.get(pytest.KEY) is False

    @pytest.mark.asyncio
    async def test_set(self, mock_cache):
        await mock_cache.set(pytest.KEY, "value", ttl=2)

        mock_cache._set.assert_called_with(
            mock_cache._build_key(pytest.KEY), ANY, ttl=2, _cas_token=None, _conn=ANY
        )
        assert mock_cache.plugins[0].pre_set.call_count == 1
        assert mock_cache.plugins[0].post_set.call_count == 1

    @pytest.mark.asyncio
    async def test_set_timeouts(self, mock_cache):
        mock_cache._set = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.set(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_add(self, mock_cache):
        mock_cache._exists = AsyncMock(return_value=False)
        await mock_cache.add(pytest.KEY, "value", ttl=2)

        key = mock_cache._build_key(pytest.KEY)
        mock_cache._add.assert_called_with(key, ANY, ttl=2, _conn=ANY)
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

        mock_cache._multi_get.assert_called_with(
            [mock_cache._build_key(pytest.KEY), mock_cache._build_key(pytest.KEY_1)],
            encoding=ANY,
            _conn=ANY,
        )
        assert mock_cache.plugins[0].pre_multi_get.call_count == 1
        assert mock_cache.plugins[0].post_multi_get.call_count == 1

    @pytest.mark.asyncio
    async def test_mget_timeouts(self, mock_cache):
        mock_cache._multi_get = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.multi_get(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_mset(self, mock_cache):
        await mock_cache.multi_set([[pytest.KEY, "value"], [pytest.KEY_1, "value1"]], ttl=2)

        mock_cache._multi_set.assert_called_with(
            [(mock_cache._build_key(pytest.KEY), ANY), (mock_cache._build_key(pytest.KEY_1), ANY)],
            ttl=2,
            _conn=ANY,
        )
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

        mock_cache._exists.assert_called_with(mock_cache._build_key(pytest.KEY), _conn=ANY)
        assert mock_cache.plugins[0].pre_exists.call_count == 1
        assert mock_cache.plugins[0].post_exists.call_count == 1

    @pytest.mark.asyncio
    async def test_exists_timeouts(self, mock_cache):
        mock_cache._exists = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.exists(pytest.KEY)

    @pytest.mark.asyncio
    async def test_increment(self, mock_cache):
        await mock_cache.increment(pytest.KEY, 2)

        mock_cache._increment.assert_called_with(mock_cache._build_key(pytest.KEY), 2, _conn=ANY)
        assert mock_cache.plugins[0].pre_increment.call_count == 1
        assert mock_cache.plugins[0].post_increment.call_count == 1

    @pytest.mark.asyncio
    async def test_increment_timeouts(self, mock_cache):
        mock_cache._increment = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.increment(pytest.KEY)

    @pytest.mark.asyncio
    async def test_delete(self, mock_cache):
        await mock_cache.delete(pytest.KEY)

        mock_cache._delete.assert_called_with(mock_cache._build_key(pytest.KEY), _conn=ANY)
        assert mock_cache.plugins[0].pre_delete.call_count == 1
        assert mock_cache.plugins[0].post_delete.call_count == 1

    @pytest.mark.asyncio
    async def test_delete_timeouts(self, mock_cache):
        mock_cache._delete = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.delete(pytest.KEY)

    @pytest.mark.asyncio
    async def test_expire(self, mock_cache):
        await mock_cache.expire(pytest.KEY, 1)
        mock_cache._expire.assert_called_with(mock_cache._build_key(pytest.KEY), 1, _conn=ANY)
        assert mock_cache.plugins[0].pre_expire.call_count == 1
        assert mock_cache.plugins[0].post_expire.call_count == 1

    @pytest.mark.asyncio
    async def test_expire_timeouts(self, mock_cache):
        mock_cache._expire = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.expire(pytest.KEY, 0)

    @pytest.mark.asyncio
    async def test_clear(self, mock_cache):
        await mock_cache.clear(pytest.KEY)
        mock_cache._clear.assert_called_with(mock_cache._build_key(pytest.KEY), _conn=ANY)
        assert mock_cache.plugins[0].pre_clear.call_count == 1
        assert mock_cache.plugins[0].post_clear.call_count == 1

    @pytest.mark.asyncio
    async def test_clear_timeouts(self, mock_cache):
        mock_cache._clear = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.clear(pytest.KEY)

    @pytest.mark.asyncio
    async def test_raw(self, mock_cache):
        await mock_cache.raw("get", pytest.KEY)
        mock_cache._raw.assert_called_with(
            "get", mock_cache._build_key(pytest.KEY), encoding=ANY, _conn=ANY
        )
        assert mock_cache.plugins[0].pre_raw.call_count == 1
        assert mock_cache.plugins[0].post_raw.call_count == 1

    @pytest.mark.asyncio
    async def test_raw_timeouts(self, mock_cache):
        mock_cache._raw = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.raw("clear")

    @pytest.mark.asyncio
    async def test_close(self, mock_cache):
        await mock_cache.close()
        assert mock_cache._close.call_count == 1

    @pytest.mark.asyncio
    async def test_get_connection(self, mock_cache):
        async with mock_cache.get_connection():
            pass
        assert mock_cache.acquire_conn.call_count == 1
        assert mock_cache.release_conn.call_count == 1


@pytest.fixture
def conn(mock_cache):
    yield _Conn(mock_cache)


class TestConn:
    def test_conn(self, conn, mock_cache):
        assert conn._cache == mock_cache

    def test_conn_getattr(self, conn, mock_cache):
        assert conn.timeout == mock_cache.timeout
        assert conn.namespace == conn.namespace
        assert conn.serializer is mock_cache.serializer

    @pytest.mark.asyncio
    async def test_conn_context_manager(self, conn):
        async with conn:
            assert conn._cache.acquire_conn.call_count == 1
        conn._cache.release_conn.assert_called_with(conn._cache.acquire_conn.return_value)

    @pytest.mark.asyncio
    async def test_inject_conn(self, conn):
        conn._conn = "connection"
        conn._cache.dummy = AsyncMock()

        await _Conn._inject_conn("dummy")(conn, "a", b="b")
        conn._cache.dummy.assert_called_with("a", _conn=conn._conn, b="b")
