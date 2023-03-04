import asyncio
import os
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from aiocache.base import API, _Conn
from ..utils import AbstractBaseCache, ConcreteBaseCache, Keys, ensure_key


class TestAPI:
    def test_register(self):
        @API.register
        def dummy():
            """Dummy function."""

        assert dummy in API.CMDS
        API.unregister(dummy)

    def test_unregister(self):
        @API.register
        def dummy():
            "Dummy function."""

        API.unregister(dummy)
        assert dummy not in API.CMDS

    def test_unregister_unexisting(self):
        def dummy():
            "Dummy function."""

        API.unregister(dummy)
        assert dummy not in API.CMDS

    async def test_aiocache_enabled(self):
        @API.aiocache_enabled()
        async def dummy(*args, **kwargs):
            return True

        assert await dummy() is True

    async def test_aiocache_enabled_disabled(self):
        @API.aiocache_enabled(fake_return=[])
        async def dummy(*args, **kwargs):
            """Dummy function."""

        with patch.dict(os.environ, {"AIOCACHE_DISABLE": "1"}):
            assert await dummy() == []

    async def test_timeout_no_timeout(self):
        self = MagicMock(spec_set=("timeout",))
        self.timeout = 0

        @API.timeout
        async def dummy(self):
            self()

        with patch("asyncio.wait_for") as wait_for:
            await dummy(self)
            assert self.call_count == 1
            assert wait_for.call_count == 0

    async def test_timeout_self(self):
        self = MagicMock(spec_set=("timeout",))
        self.timeout = 0.002

        @API.timeout
        async def dummy(self):
            await asyncio.sleep(0.005)

        with pytest.raises(asyncio.TimeoutError):
            await dummy(self)

    async def test_timeout_kwarg_0(self):
        self = MagicMock(spec_set=("timeout",))
        self.timeout = 0.002

        @API.timeout
        async def dummy(self):
            await asyncio.sleep(0.005)
            return True

        assert await dummy(self, timeout=0) is True

    async def test_timeout_kwarg_None(self):
        self = MagicMock(spec_set=("timeout",))
        self.timeout = 0.002

        @API.timeout
        async def dummy(self):
            await asyncio.sleep(0.005)
            return True

        assert await dummy(self, timeout=None) is True

    async def test_timeout_kwarg(self):
        self = MagicMock(spec_set=("timeout",))

        @API.timeout
        async def dummy(self):
            await asyncio.sleep(0.005)

        with pytest.raises(asyncio.TimeoutError):
            await dummy(self, timeout=0.002)

    async def test_timeout_self_kwarg(self):
        self = MagicMock(spec_set=("timeout",))
        self.timeout = 5

        @API.timeout
        async def dummy(self):
            await asyncio.sleep(0.005)

        with pytest.raises(asyncio.TimeoutError):
            await dummy(self, timeout=0.003)

    async def test_plugins(self):
        self = MagicMock(spec_set=("plugins",))
        plugin1 = MagicMock(spec_set=("pre_dummy", "post_dummy"))
        plugin1.pre_dummy = AsyncMock(spec_set=())
        plugin1.post_dummy = AsyncMock(spec_set=())
        plugin2 = MagicMock(spec_set=("pre_dummy", "post_dummy"))
        plugin2.pre_dummy = AsyncMock(spec_set=())
        plugin2.post_dummy = AsyncMock(spec_set=())
        self.plugins = (plugin1, plugin2)

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
        cache = AbstractBaseCache(ttl="1.5")
        assert cache.ttl == 1.5

    def test_str_timeout(self):
        cache = AbstractBaseCache(timeout="1.5")
        assert cache.timeout == 1.5

    async def test_add(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._add(Keys.KEY, "value", 0)

    async def test_get(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._get(Keys.KEY, "utf-8")

    async def test_set(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._set(Keys.KEY, "value", 0)

    async def test_multi_get(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._multi_get([Keys.KEY], encoding="utf-8")

    async def test_multi_set(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._multi_set([(Keys.KEY, "value")], 0)

    async def test_delete(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._delete(Keys.KEY)

    async def test_exists(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._exists(Keys.KEY)

    async def test_increment(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._increment(Keys.KEY, 2)

    async def test_expire(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._expire(Keys.KEY, 0)

    async def test_clear(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._clear("namespace")

    async def test_raw(self, base_cache):
        with pytest.raises(NotImplementedError):
            await base_cache._raw("get", Keys.KEY)

    async def test_close(self, base_cache):
        assert await base_cache._close() is None

    async def test_acquire_conn(self, base_cache):
        assert await base_cache.acquire_conn() == base_cache

    async def test_release_conn(self, base_cache):
        assert await base_cache.release_conn("mock") is None

    def test_abstract_build_key(self, abstract_base_cache):
        with pytest.raises(NotImplementedError):
            abstract_base_cache.build_key(Keys.KEY)

    @pytest.fixture
    def set_test_namespace(self, base_cache):
        base_cache.namespace = "test"
        yield
        base_cache.namespace = ""

    @pytest.mark.parametrize(
        "namespace, expected",
        ([None, "None" + ensure_key(Keys.KEY)], ["", ensure_key(Keys.KEY)], ["my_ns", "my_ns" + ensure_key(Keys.KEY)]),  # noqa: B950
    )
    def test_str_build_key(self, set_test_namespace, namespace, expected):
        # TODO: Runtime check for namespace=None: Raise ValueError or replace with ""?
        cache = AbstractBaseCache(namespace=namespace)
        assert cache._str_build_key(Keys.KEY) == expected

    @pytest.mark.parametrize(
        "namespace, expected",
        ([None, "test" + ensure_key(Keys.KEY)], ["", ensure_key(Keys.KEY)], ["my_ns", "my_ns" + ensure_key(Keys.KEY)]),  # noqa: B950
    )
    def test_build_key(self, set_test_namespace, base_cache, namespace, expected):
        assert base_cache.build_key(Keys.KEY, namespace) == expected

    def test_alt_build_key(self):
        cache = ConcreteBaseCache(key_builder=lambda key, namespace: "x")
        assert cache.build_key(Keys.KEY, "namespace") == "x"

    def alt_build_key(self, key, namespace):
        """Custom key_builder for cache"""
        sep = ":" if namespace else ""
        return f"{namespace}{sep}{ensure_key(key)}"

    @pytest.mark.parametrize(
        "namespace, expected",
        ([None, "test:" + ensure_key(Keys.KEY)], ["", ensure_key(Keys.KEY)], ["my_ns", "my_ns:" + ensure_key(Keys.KEY)]),  # noqa: B950
    )
    def test_alt_build_key_override_namespace(self, namespace, expected):
        """Custom key_builder overrides namespace of cache"""
        cache = ConcreteBaseCache(key_builder=self.alt_build_key, namespace="test")
        assert cache.build_key(Keys.KEY, namespace) == expected

    @pytest.mark.parametrize(
        "namespace, expected",
        ([None, "None" + ensure_key(Keys.KEY)], ["", ensure_key(Keys.KEY)], ["test", "test:" + ensure_key(Keys.KEY)]),  # noqa: B950
    )
    async def test_alt_build_key_default_namespace(self, namespace, expected):
        """Custom key_builder for cache with or without namespace specified.

        Cache member functions that accept a ``namespace`` parameter
        should default to using ``self.namespace`` if the ``namespace``
        argument is ``None``.

        This enables a cache to correctly build keys when the cache is
        initialized with both a ``namespace`` and a ``key_builder``,
        even when that cache is supplied to a lock or to a decorator
        using the ``alias`` argument.
        """
        cache = ConcreteBaseCache(key_builder=self.alt_build_key, namespace=namespace)

        # Verify that private members are called with the correct ns_key
        await self._assert_add__alt_build_key_default_namespace(cache, expected)
        await self._assert_get__alt_build_key_default_namespace(cache, expected)
        await self._assert_multi_get__alt_build_key_default_namespace(cache, expected)
        await self._assert_set__alt_build_key_default_namespace(cache, expected)
        await self._assert_multi_set__alt_build_key_default_namespace(cache, expected)
        await self._assert_exists__alt_build_key_default_namespace(cache, expected)
        await self._assert_increment__alt_build_key_default_namespace(cache, expected)
        await self._assert_delete__alt_build_key_default_namespace(cache, expected)
        await self._assert_expire__alt_build_key_default_namespace(cache, expected)

    async def _assert_add__alt_build_key_default_namespace(self, cache, expected):
        with patch.object(cache, "_add", autospec=True) as _add:
            await cache.add(Keys.KEY, "value")
            _add.assert_called_once_with(expected, "value", _conn=None, ttl=None)

    async def _assert_get__alt_build_key_default_namespace(self, cache, expected):
        with patch.object(cache, "_get", autospec=True) as _get:
            await cache.get(Keys.KEY)
            _get.assert_called_once_with(
                expected, _conn=None, encoding=cache.serializer.encoding)

    async def _assert_multi_get__alt_build_key_default_namespace(self, cache, expected):
        with patch.object(cache, "_multi_get", autospec=True) as _multi_get:
            await cache.multi_get([Keys.KEY])
            _multi_get.assert_called_once_with(
                [expected], _conn=None, encoding=cache.serializer.encoding)

    async def _assert_set__alt_build_key_default_namespace(self, cache, expected):
        with patch.object(cache, "_set", autospec=True) as _set:
            await cache.set(Keys.KEY, "value")
            _set.assert_called_once_with(
                expected, "value", _conn=None, ttl=None, _cas_token=None)

    async def _assert_multi_set__alt_build_key_default_namespace(self, cache, expected):
        with patch.object(cache, "_multi_set", autospec=True) as _multi_set:
            await cache.multi_set([(Keys.KEY, "value")])
            _multi_set.assert_called_once_with(
                [(expected, "value")], _conn=None, ttl=None)

    async def _assert_exists__alt_build_key_default_namespace(self, cache, expected):
        with patch.object(cache, "_exists", autospec=True) as _exists:
            await cache.exists(Keys.KEY)
            _exists.assert_called_once_with(expected, _conn=None)

    async def _assert_increment__alt_build_key_default_namespace(self, cache, expected):
        with patch.object(cache, "_increment", autospec=True) as _increment:
            await cache.increment(Keys.KEY)
            _increment.assert_called_once_with(expected, delta=1, _conn=None)

    async def _assert_delete__alt_build_key_default_namespace(self, cache, expected):
        with patch.object(cache, "_delete", autospec=True) as _delete:
            await cache.delete(Keys.KEY)
            _delete.assert_called_once_with(expected, _conn=None)

    async def _assert_expire__alt_build_key_default_namespace(self, cache, expected):
        with patch.object(cache, "_expire", autospec=True) as _expire:
            await cache.expire(Keys.KEY, 0)
            _expire.assert_called_once_with(expected, 0, _conn=None)

    async def test_add_ttl_cache_default(self, base_cache):
        with patch.object(base_cache, "_add", autospec=True) as m:
            await base_cache.add(Keys.KEY, "value")

            m.assert_called_once_with(Keys.KEY, "value", _conn=None, ttl=None)

    async def test_add_ttl_default(self, base_cache):
        base_cache.ttl = 10
        with patch.object(base_cache, "_add", autospec=True) as m:
            await base_cache.add(Keys.KEY, "value")

            m.assert_called_once_with(Keys.KEY, "value", _conn=None, ttl=10)

    async def test_add_ttl_overriden(self, base_cache):
        base_cache.ttl = 10
        with patch.object(base_cache, "_add", autospec=True) as m:
            await base_cache.add(Keys.KEY, "value", ttl=20)

            m.assert_called_once_with(Keys.KEY, "value", _conn=None, ttl=20)

    async def test_add_ttl_none(self, base_cache):
        base_cache.ttl = 10
        with patch.object(base_cache, "_add", autospec=True) as m:
            await base_cache.add(Keys.KEY, "value", ttl=None)

            m.assert_called_once_with(Keys.KEY, "value", _conn=None, ttl=None)

    async def test_set_ttl_cache_default(self, base_cache):
        with patch.object(base_cache, "_set", autospec=True) as m:
            await base_cache.set(Keys.KEY, "value")

            m.assert_called_once_with(
                Keys.KEY, "value", _cas_token=None, _conn=None, ttl=None
            )

    async def test_set_ttl_default(self, base_cache):
        base_cache.ttl = 10
        with patch.object(base_cache, "_set", autospec=True) as m:
            await base_cache.set(Keys.KEY, "value")

            m.assert_called_once_with(
                Keys.KEY, "value", _cas_token=None, _conn=None, ttl=10
            )

    async def test_set_ttl_overriden(self, base_cache):
        base_cache.ttl = 10
        with patch.object(base_cache, "_set", autospec=True) as m:
            await base_cache.set(Keys.KEY, "value", ttl=20)

            m.assert_called_once_with(
                Keys.KEY, "value", _cas_token=None, _conn=None, ttl=20
            )

    async def test_set_ttl_none(self, base_cache):
        base_cache.ttl = 10
        with patch.object(base_cache, "_set", autospec=True) as m:
            await base_cache.set(Keys.KEY, "value", ttl=None)

            m.assert_called_once_with(
                Keys.KEY, "value", _cas_token=None, _conn=None, ttl=None
            )

    async def test_multi_set_ttl_cache_default(self, base_cache):
        with patch.object(base_cache, "_multi_set", autospec=True) as m:
            await base_cache.multi_set([[Keys.KEY, "value"], [Keys.KEY_1, "value1"]])

            m.assert_called_once_with(
                [(Keys.KEY, "value"), (Keys.KEY_1, "value1")], _conn=None, ttl=None
            )

    async def test_multi_set_ttl_default(self, base_cache):
        base_cache.ttl = 10
        with patch.object(base_cache, "_multi_set", autospec=True) as m:
            await base_cache.multi_set([[Keys.KEY, "value"], [Keys.KEY_1, "value1"]])

            m.assert_called_once_with(
                [(Keys.KEY, "value"), (Keys.KEY_1, "value1")], _conn=None, ttl=10
            )

    async def test_multi_set_ttl_overriden(self, base_cache):
        base_cache.ttl = 10
        with patch.object(base_cache, "_multi_set", autospec=True) as m:
            await base_cache.multi_set([[Keys.KEY, "value"], [Keys.KEY_1, "value1"]], ttl=20)

            m.assert_called_once_with(
                [(Keys.KEY, "value"), (Keys.KEY_1, "value1")], _conn=None, ttl=20
            )

    async def test_multi_set_ttl_none(self, base_cache):
        base_cache.ttl = 10
        with patch.object(base_cache, "_multi_set", autospec=True) as m:
            await base_cache.multi_set([[Keys.KEY, "value"], [Keys.KEY_1, "value1"]], ttl=None)

            m.assert_called_once_with(
                [(Keys.KEY, "value"), (Keys.KEY_1, "value1")], _conn=None, ttl=None
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

    async def test_get(self, mock_base_cache):
        await mock_base_cache.get(Keys.KEY)

        mock_base_cache._get.assert_called_with(
            mock_base_cache.build_key(Keys.KEY), encoding=ANY, _conn=ANY
        )
        assert mock_base_cache.plugins[0].pre_get.call_count == 1
        assert mock_base_cache.plugins[0].post_get.call_count == 1

    async def test_get_timeouts(self, mock_base_cache):
        mock_base_cache._get = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_base_cache.get(Keys.KEY)

    async def test_get_default(self, mock_base_cache):
        mock_base_cache._serializer.loads.return_value = None

        assert await mock_base_cache.get(Keys.KEY, default=1) == 1

    async def test_get_negative_default(self, mock_base_cache):
        mock_base_cache._serializer.loads.return_value = False

        assert await mock_base_cache.get(Keys.KEY) is False

    async def test_set(self, mock_base_cache):
        await mock_base_cache.set(Keys.KEY, "value", ttl=2)

        mock_base_cache._set.assert_called_with(
            mock_base_cache.build_key(Keys.KEY), ANY, ttl=2, _cas_token=None, _conn=ANY
        )
        assert mock_base_cache.plugins[0].pre_set.call_count == 1
        assert mock_base_cache.plugins[0].post_set.call_count == 1

    async def test_set_timeouts(self, mock_base_cache):
        mock_base_cache._set = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_base_cache.set(Keys.KEY, "value")

    async def test_add(self, mock_base_cache):
        mock_base_cache._exists = AsyncMock(return_value=False)
        await mock_base_cache.add(Keys.KEY, "value", ttl=2)

        key = mock_base_cache.build_key(Keys.KEY)
        mock_base_cache._add.assert_called_with(key, ANY, ttl=2, _conn=ANY)
        assert mock_base_cache.plugins[0].pre_add.call_count == 1
        assert mock_base_cache.plugins[0].post_add.call_count == 1

    async def test_add_timeouts(self, mock_base_cache):
        mock_base_cache._add = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_base_cache.add(Keys.KEY, "value")

    async def test_mget(self, mock_base_cache):
        await mock_base_cache.multi_get([Keys.KEY, Keys.KEY_1])

        mock_base_cache._multi_get.assert_called_with(
            [mock_base_cache.build_key(Keys.KEY), mock_base_cache.build_key(Keys.KEY_1)],
            encoding=ANY,
            _conn=ANY,
        )
        assert mock_base_cache.plugins[0].pre_multi_get.call_count == 1
        assert mock_base_cache.plugins[0].post_multi_get.call_count == 1

    async def test_mget_timeouts(self, mock_base_cache):
        mock_base_cache._multi_get = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_base_cache.multi_get(Keys.KEY, "value")

    async def test_mset(self, mock_base_cache):
        await mock_base_cache.multi_set([[Keys.KEY, "value"], [Keys.KEY_1, "value1"]], ttl=2)

        key = mock_base_cache.build_key(Keys.KEY)
        key1 = mock_base_cache.build_key(Keys.KEY_1)
        mock_base_cache._multi_set.assert_called_with(
            [(key, ANY), (key1, ANY)], ttl=2, _conn=ANY)
        assert mock_base_cache.plugins[0].pre_multi_set.call_count == 1
        assert mock_base_cache.plugins[0].post_multi_set.call_count == 1

    async def test_mset_timeouts(self, mock_base_cache):
        mock_base_cache._multi_set = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_base_cache.multi_set([[Keys.KEY, "value"], [Keys.KEY_1, "value1"]])

    async def test_exists(self, mock_base_cache):
        await mock_base_cache.exists(Keys.KEY)

        mock_base_cache._exists.assert_called_with(mock_base_cache.build_key(Keys.KEY), _conn=ANY)
        assert mock_base_cache.plugins[0].pre_exists.call_count == 1
        assert mock_base_cache.plugins[0].post_exists.call_count == 1

    async def test_exists_timeouts(self, mock_base_cache):
        mock_base_cache._exists = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_base_cache.exists(Keys.KEY)

    async def test_increment(self, mock_base_cache):
        await mock_base_cache.increment(Keys.KEY, 2)

        key = mock_base_cache.build_key(Keys.KEY)
        mock_base_cache._increment.assert_called_with(key, 2, _conn=ANY)
        assert mock_base_cache.plugins[0].pre_increment.call_count == 1
        assert mock_base_cache.plugins[0].post_increment.call_count == 1

    async def test_increment_timeouts(self, mock_base_cache):
        mock_base_cache._increment = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_base_cache.increment(Keys.KEY)

    async def test_delete(self, mock_base_cache):
        await mock_base_cache.delete(Keys.KEY)

        mock_base_cache._delete.assert_called_with(mock_base_cache.build_key(Keys.KEY), _conn=ANY)
        assert mock_base_cache.plugins[0].pre_delete.call_count == 1
        assert mock_base_cache.plugins[0].post_delete.call_count == 1

    async def test_delete_timeouts(self, mock_base_cache):
        mock_base_cache._delete = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_base_cache.delete(Keys.KEY)

    async def test_expire(self, mock_base_cache):
        await mock_base_cache.expire(Keys.KEY, 1)
        key = mock_base_cache.build_key(Keys.KEY)
        mock_base_cache._expire.assert_called_with(key, 1, _conn=ANY)
        assert mock_base_cache.plugins[0].pre_expire.call_count == 1
        assert mock_base_cache.plugins[0].post_expire.call_count == 1

    async def test_expire_timeouts(self, mock_base_cache):
        mock_base_cache._expire = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_base_cache.expire(Keys.KEY, 0)

    async def test_clear(self, mock_base_cache):
        await mock_base_cache.clear(Keys.KEY)
        mock_base_cache._clear.assert_called_with(mock_base_cache.build_key(Keys.KEY), _conn=ANY)
        assert mock_base_cache.plugins[0].pre_clear.call_count == 1
        assert mock_base_cache.plugins[0].post_clear.call_count == 1

    async def test_clear_timeouts(self, mock_base_cache):
        mock_base_cache._clear = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_base_cache.clear(Keys.KEY)

    async def test_raw(self, mock_base_cache):
        await mock_base_cache.raw("get", Keys.KEY)
        mock_base_cache._raw.assert_called_with(
            "get", mock_base_cache.build_key(Keys.KEY), encoding=ANY, _conn=ANY
        )
        assert mock_base_cache.plugins[0].pre_raw.call_count == 1
        assert mock_base_cache.plugins[0].post_raw.call_count == 1

    async def test_raw_timeouts(self, mock_base_cache):
        mock_base_cache._raw = self.asleep

        with pytest.raises(asyncio.TimeoutError):
            await mock_base_cache.raw("clear")

    async def test_close(self, mock_base_cache):
        await mock_base_cache.close()
        assert mock_base_cache._close.call_count == 1

    async def test_get_connection(self, mock_base_cache):
        async with mock_base_cache.get_connection():
            pass
        assert mock_base_cache.acquire_conn.call_count == 1
        assert mock_base_cache.release_conn.call_count == 1


@pytest.fixture
def conn(mock_base_cache):
    yield _Conn(mock_base_cache)


class TestConn:
    def test_conn(self, conn, mock_base_cache):
        assert conn._cache == mock_base_cache

    def test_conn_getattr(self, conn, mock_base_cache):
        assert conn.timeout == mock_base_cache.timeout
        assert conn.namespace == mock_base_cache.namespace
        assert conn.serializer is mock_base_cache.serializer

    async def test_conn_context_manager(self, conn):
        async with conn:
            assert conn._cache.acquire_conn.call_count == 1
        conn._cache.release_conn.assert_called_with(conn._cache.acquire_conn.return_value)

    async def test_inject_conn(self, conn):
        conn._conn = "connection"
        conn._cache.dummy = AsyncMock(spec_set=())
        await _Conn._inject_conn("dummy")(conn, "a", b="b")
        conn._cache.dummy.assert_called_with("a", _conn=conn._conn, b="b")
