from unittest.mock import AsyncMock, patch

import aiomcache
import pytest

from aiocache.backends.memcached import MemcachedBackend, MemcachedCache
from aiocache.base import BaseCache
from aiocache.serializers import JsonSerializer
from ...utils import Keys, ensure_key


@pytest.fixture
def memcached():
    memcached = MemcachedBackend()
    with patch.object(memcached, "client", autospec=True) as m:
        # Autospec messes up the signature on the decorated methods.
        for method in (
            "get", "gets", "multi_get", "stats", "set", "cas", "replace",
            "append", "prepend", "incr", "decr", "touch", "version", "flush_all"
        ):
            setattr(m, method, AsyncMock(return_value=None, spec_set=()))
        m.add = AsyncMock(return_value=True, spec_set=())
        m.delete = AsyncMock(return_value=True, spec_set=())

        yield memcached


class TestMemcachedBackend:
    def test_setup(self):
        with patch.object(aiomcache, "Client", autospec=True) as aiomcache_client:
            memcached = MemcachedBackend()

            aiomcache_client.assert_called_with("127.0.0.1", 11211, pool_size=2)

        assert memcached.endpoint == "127.0.0.1"
        assert memcached.port == 11211
        assert memcached.pool_size == 2

    def test_setup_override(self):
        with patch.object(aiomcache, "Client", autospec=True) as aiomcache_client:
            memcached = MemcachedBackend(endpoint="127.0.0.2", port=2, pool_size=10)

            aiomcache_client.assert_called_with("127.0.0.2", 2, pool_size=10)

        assert memcached.endpoint == "127.0.0.2"
        assert memcached.port == 2
        assert memcached.pool_size == 10

    def test_setup_casts(self):
        with patch.object(aiomcache, "Client", autospec=True) as aiomcache_client:
            memcached = MemcachedBackend(pool_size="10")

            aiomcache_client.assert_called_with("127.0.0.1", 11211, pool_size=10)

        assert memcached.pool_size == 10

    async def test_get(self, memcached):
        memcached.client.get.return_value = b"value"
        assert await memcached._get(Keys.KEY) == "value"
        memcached.client.get.assert_called_with(Keys.KEY)

    async def test_gets(self, memcached):
        memcached.client.gets.return_value = b"value", 12345
        assert await memcached._gets(Keys.KEY) == 12345
        memcached.client.gets.assert_called_with(Keys.KEY.encode())

    async def test_get_none(self, memcached):
        memcached.client.get.return_value = None
        assert await memcached._get(Keys.KEY) is None
        memcached.client.get.assert_called_with(Keys.KEY)

    async def test_get_no_encoding(self, memcached):
        memcached.client.get.return_value = b"value"
        assert await memcached._get(Keys.KEY, encoding=None) == b"value"
        memcached.client.get.assert_called_with(Keys.KEY)

    async def test_set(self, memcached):
        await memcached._set(Keys.KEY, "value")
        memcached.client.set.assert_called_with(Keys.KEY, b"value", exptime=0)

        await memcached._set(Keys.KEY, "value", ttl=1)
        memcached.client.set.assert_called_with(Keys.KEY, b"value", exptime=1)

    async def test_set_float_ttl(self, memcached):
        memcached.client.set.side_effect = aiomcache.exceptions.ValidationException("msg")
        with pytest.raises(TypeError) as exc_info:
            await memcached._set(Keys.KEY, "value", ttl=0.1)
        assert str(exc_info.value) == "aiomcache error: msg"

    async def test_set_cas_token(self, mocker, memcached):
        mocker.spy(memcached, "_cas")
        await memcached._set(Keys.KEY, "value", _cas_token="token")
        memcached._cas.assert_called_with(Keys.KEY, b"value", "token", ttl=0, _conn=None)

    async def test_cas(self, memcached):
        memcached.client.cas.return_value = True
        assert await memcached._cas(Keys.KEY, b"value", "token", ttl=0) is True
        memcached.client.cas.assert_called_with(Keys.KEY, b"value", "token", exptime=0)

    async def test_cas_fail(self, memcached):
        memcached.client.cas.return_value = False
        assert await memcached._cas(Keys.KEY, b"value", "token", ttl=0) is False
        memcached.client.cas.assert_called_with(Keys.KEY, b"value", "token", exptime=0)

    async def test_multi_get(self, memcached):
        memcached.client.multi_get.return_value = [b"value", b"random"]
        assert await memcached._multi_get([Keys.KEY, Keys.KEY_1]) == ["value", "random"]
        memcached.client.multi_get.assert_called_with(Keys.KEY, Keys.KEY_1)

    async def test_multi_get_none(self, memcached):
        memcached.client.multi_get.return_value = [b"value", None]
        assert await memcached._multi_get([Keys.KEY, Keys.KEY_1]) == ["value", None]
        memcached.client.multi_get.assert_called_with(Keys.KEY, Keys.KEY_1)

    async def test_multi_get_no_encoding(self, memcached):
        memcached.client.multi_get.return_value = [b"value", None]
        assert await memcached._multi_get([Keys.KEY, Keys.KEY_1], encoding=None) == [
            b"value",
            None,
        ]
        memcached.client.multi_get.assert_called_with(Keys.KEY, Keys.KEY_1)

    async def test_multi_set(self, memcached):
        await memcached._multi_set([(Keys.KEY, "value"), (Keys.KEY_1, "random")])
        memcached.client.set.assert_any_call(Keys.KEY, b"value", exptime=0)
        memcached.client.set.assert_any_call(Keys.KEY_1, b"random", exptime=0)
        assert memcached.client.set.call_count == 2

        await memcached._multi_set([(Keys.KEY, "value"), (Keys.KEY_1, "random")], ttl=1)
        memcached.client.set.assert_any_call(Keys.KEY, b"value", exptime=1)
        memcached.client.set.assert_any_call(Keys.KEY_1, b"random", exptime=1)
        assert memcached.client.set.call_count == 4

    async def test_multi_set_float_ttl(self, memcached):
        memcached.client.set.side_effect = aiomcache.exceptions.ValidationException("msg")
        with pytest.raises(TypeError) as exc_info:
            await memcached._multi_set([(Keys.KEY, "value"), (Keys.KEY_1, "random")], ttl=0.1)
        assert str(exc_info.value) == "aiomcache error: msg"

    async def test_add(self, memcached):
        await memcached._add(Keys.KEY, "value")
        memcached.client.add.assert_called_with(Keys.KEY, b"value", exptime=0)

        await memcached._add(Keys.KEY, "value", ttl=1)
        memcached.client.add.assert_called_with(Keys.KEY, b"value", exptime=1)

    async def test_add_existing(self, memcached):
        memcached.client.add.return_value = False
        with pytest.raises(ValueError):
            await memcached._add(Keys.KEY, "value")

    async def test_add_float_ttl(self, memcached):
        memcached.client.add.side_effect = aiomcache.exceptions.ValidationException("msg")
        with pytest.raises(TypeError) as exc_info:
            await memcached._add(Keys.KEY, "value", 0.1)
        assert str(exc_info.value) == "aiomcache error: msg"

    async def test_exists(self, memcached):
        await memcached._exists(Keys.KEY)
        memcached.client.append.assert_called_with(Keys.KEY, b"")

    async def test_increment(self, memcached):
        await memcached._increment(Keys.KEY, 2)
        memcached.client.incr.assert_called_with(Keys.KEY, 2)

    async def test_increment_negative(self, memcached):
        await memcached._increment(Keys.KEY, -2)
        memcached.client.decr.assert_called_with(Keys.KEY, 2)

    async def test_increment_missing(self, memcached):
        memcached.client.incr.side_effect = aiomcache.exceptions.ClientException("NOT_FOUND")
        await memcached._increment(Keys.KEY, 2)
        memcached.client.incr.assert_called_with(Keys.KEY, 2)
        memcached.client.set.assert_called_with(Keys.KEY, b"2", exptime=0)

    async def test_increment_missing_negative(self, memcached):
        memcached.client.decr.side_effect = aiomcache.exceptions.ClientException("NOT_FOUND")
        await memcached._increment(Keys.KEY, -2)
        memcached.client.decr.assert_called_with(Keys.KEY, 2)
        memcached.client.set.assert_called_with(Keys.KEY, b"-2", exptime=0)

    async def test_increment_typerror(self, memcached):
        memcached.client.incr.side_effect = aiomcache.exceptions.ClientException("msg")
        with pytest.raises(TypeError) as exc_info:
            await memcached._increment(Keys.KEY, 2)
        assert str(exc_info.value) == "aiomcache error: msg"

    async def test_expire(self, memcached):
        await memcached._expire(Keys.KEY, 1)
        memcached.client.touch.assert_called_with(Keys.KEY, 1)

    async def test_delete(self, memcached):
        assert await memcached._delete(Keys.KEY) == 1
        memcached.client.delete.assert_called_with(Keys.KEY)

    async def test_delete_missing(self, memcached):
        memcached.client.delete.return_value = False
        assert await memcached._delete(Keys.KEY) == 0
        memcached.client.delete.assert_called_with(Keys.KEY)

    async def test_clear(self, memcached):
        await memcached._clear()
        memcached.client.flush_all.assert_called_with()

    async def test_clear_with_namespace(self, memcached):
        with pytest.raises(ValueError):
            await memcached._clear("nm")

    async def test_raw(self, memcached):
        await memcached._raw("get", Keys.KEY)
        await memcached._raw("set", Keys.KEY, 1)
        memcached.client.get.assert_called_with(Keys.KEY)
        memcached.client.set.assert_called_with(Keys.KEY, 1)

    async def test_raw_bytes(self, memcached):
        await memcached._raw("set", Keys.KEY, "asd")
        await memcached._raw("get", Keys.KEY, encoding=None)
        memcached.client.get.assert_called_with(Keys.KEY)
        memcached.client.set.assert_called_with(Keys.KEY, "asd")

    async def test_redlock_release(self, mocker, memcached):
        mocker.spy(memcached, "_delete")
        await memcached._redlock_release(Keys.KEY, "random")
        memcached._delete.assert_called_with(Keys.KEY)

    async def test_close(self, memcached):
        await memcached._close()
        assert memcached.client.close.call_count == 1


class TestMemcachedCache:
    @pytest.fixture
    def set_test_namespace(self, memcached_cache):
        memcached_cache.namespace = "test"
        yield
        memcached_cache.namespace = None

    def test_name(self):
        assert MemcachedCache.NAME == "memcached"

    def test_inheritance(self):
        assert isinstance(MemcachedCache(), BaseCache)

    def test_default_serializer(self):
        assert isinstance(MemcachedCache().serializer, JsonSerializer)

    def test_parse_uri_path(self):
        assert MemcachedCache().parse_uri_path("/1/2/3") == {}

    @pytest.mark.parametrize(
        "namespace, expected",
        ([None, "test" + ensure_key(Keys.KEY)], ["", ensure_key(Keys.KEY)], ["my_ns", "my_ns" + ensure_key(Keys.KEY)]),  # noqa: B950
    )
    def test_build_key_bytes(self, set_test_namespace, memcached_cache, namespace, expected):
        assert memcached_cache.build_key(Keys.KEY, namespace) == expected.encode()

    def test_build_key_no_namespace(self, memcached_cache):
        assert memcached_cache.build_key(Keys.KEY, namespace=None) == Keys.KEY.encode()

    def test_build_key_no_spaces(self, memcached_cache):
        assert memcached_cache.build_key("hello world") == b"hello_world"
