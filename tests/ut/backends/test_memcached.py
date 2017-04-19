import pytest
import aiomcache

from asynctest import MagicMock, patch, ANY

from aiocache import settings, MemcachedCache
from aiocache.backends import MemcachedBackend


@pytest.fixture
def set_settings():
    settings.set_cache(
        MemcachedCache,
        endpoint="endpoint",
        port="port",
        pool_size=12,
    )
    yield


@pytest.fixture
def memcached(event_loop):
    memcached = MemcachedBackend(loop=event_loop)
    memcached.client = MagicMock(spec=aiomcache.Client)
    yield memcached


class TestMemcachedBackend:

    def test_setup(self):
        with patch.object(aiomcache, "Client", autospec=True) as aiomcache_client:
            memory_backend = MemcachedBackend()

            aiomcache_client.assert_called_with("127.0.0.1", 11211, loop=ANY, pool_size=2)

        assert memory_backend.endpoint == "127.0.0.1"
        assert memory_backend.port == 11211

    def test_setup_override(self):
        with patch.object(aiomcache, "Client", autospec=True) as aiomcache_client:
            memory_backend = MemcachedBackend(
                endpoint="127.0.0.2",
                port=2,
                pool_size=10)

            aiomcache_client.assert_called_with("127.0.0.2", 2, loop=ANY, pool_size=10)

        assert memory_backend.endpoint == "127.0.0.2"
        assert memory_backend.port == 2

    def test_setup_default_settings(self, set_settings):
        with patch.object(aiomcache, "Client", autospec=True) as aiomcache_client:
            memory_backend = MemcachedBackend()

            aiomcache_client.assert_called_with("endpoint", "port", loop=ANY, pool_size=12)

        assert memory_backend.endpoint == "endpoint"
        assert memory_backend.port == "port"

    def test_setup_default_settings_kwargs_override(self, set_settings):
        with patch.object(aiomcache, "Client", autospec=True) as aiomcache_client:
            memory_backend = MemcachedBackend(
                endpoint="a")

            aiomcache_client.assert_called_with("a", "port", loop=ANY, pool_size=12)

        assert memory_backend.endpoint == "a"
        assert memory_backend.port == "port"

    def test_setup_default_ignored_wrong_class(self, set_settings):
        settings._CACHE = str

        with patch.object(aiomcache, "Client", autospec=True) as aiomcache_client:
            memory_backend = MemcachedBackend()

            aiomcache_client.assert_called_with("127.0.0.1", 11211, loop=ANY, pool_size=2)

        assert memory_backend.endpoint == "127.0.0.1"
        assert memory_backend.port == 11211

    @pytest.mark.asyncio
    async def test_get(self, memcached):
        memcached.client.get.return_value = b"value"
        assert await memcached._get(pytest.KEY) == "value"
        memcached.client.get.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_get_none(self, memcached):
        memcached.client.get.return_value = None
        assert await memcached._get(pytest.KEY) is None
        memcached.client.get.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_get_no_encoding(self, memcached):
        memcached.encoding = None
        memcached.client.get.return_value = b"value"
        assert await memcached._get(pytest.KEY) == b"value"
        memcached.client.get.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_set(self, memcached):
        await memcached._set(pytest.KEY, "value")
        memcached.client.set.assert_called_with(pytest.KEY, b"value", exptime=0)

        await memcached._set(pytest.KEY, "value", ttl=1)
        memcached.client.set.assert_called_with(pytest.KEY, b"value", exptime=1)

    @pytest.mark.asyncio
    async def test_multi_get(self, memcached):
        memcached.client.multi_get.return_value = [b"value", b"random"]
        assert await memcached._multi_get([pytest.KEY, pytest.KEY_1]) == ["value", "random"]
        memcached.client.multi_get.assert_called_with(pytest.KEY, pytest.KEY_1)

    @pytest.mark.asyncio
    async def test_multi_get_none(self, memcached):
        memcached.client.multi_get.return_value = [b"value", None]
        assert await memcached._multi_get([pytest.KEY, pytest.KEY_1]) == ["value", None]
        memcached.client.multi_get.assert_called_with(pytest.KEY, pytest.KEY_1)

    @pytest.mark.asyncio
    async def test_multi_get_no_encoding(self, memcached):
        memcached.encoding = None
        memcached.client.multi_get.return_value = [b"value", None]
        assert await memcached._multi_get([pytest.KEY, pytest.KEY_1]) == [b"value", None]
        memcached.client.multi_get.assert_called_with(pytest.KEY, pytest.KEY_1)

    @pytest.mark.asyncio
    async def test_multi_set(self, memcached):
        await memcached._multi_set([(pytest.KEY, "value"), (pytest.KEY_1, "random")])
        memcached.client.set.assert_any_call(pytest.KEY, b"value", exptime=0)
        memcached.client.set.assert_any_call(pytest.KEY_1, b"random", exptime=0)
        assert memcached.client.set.call_count == 2

        await memcached._multi_set([(pytest.KEY, "value"), (pytest.KEY_1, "random")], ttl=1)
        memcached.client.set.assert_any_call(pytest.KEY, b"value", exptime=1)
        memcached.client.set.assert_any_call(pytest.KEY_1, b"random", exptime=1)
        assert memcached.client.set.call_count == 4

    @pytest.mark.asyncio
    async def test_add(self, memcached):
        await memcached._add(pytest.KEY, "value")
        memcached.client.add.assert_called_with(pytest.KEY, b"value", exptime=0)

        await memcached._add(pytest.KEY, "value", ttl=1)
        memcached.client.add.assert_called_with(pytest.KEY, b"value", exptime=1)

    @pytest.mark.asyncio
    async def test_add_existing(self, memcached):
        memcached.client.add.return_value = False
        with pytest.raises(ValueError):
            await memcached._add(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_exists(self, memcached):
        await memcached._exists(pytest.KEY)
        memcached.client.append.assert_called_with(pytest.KEY, b'')

    @pytest.mark.asyncio
    async def test_increment(self, memcached):
        await memcached._increment(pytest.KEY, 2)
        memcached.client.incr.assert_called_with(pytest.KEY, 2)

    @pytest.mark.asyncio
    async def test_increment_negative(self, memcached):
        await memcached._increment(pytest.KEY, -2)
        memcached.client.decr.assert_called_with(pytest.KEY, 2)

    @pytest.mark.asyncio
    async def test_increment_missing(self, memcached):
        memcached.client.incr.side_effect = aiomcache.exceptions.ClientException("NOT_FOUND")
        await memcached._increment(pytest.KEY, 2)
        memcached.client.incr.assert_called_with(pytest.KEY, 2)
        memcached.client.set.assert_called_with(pytest.KEY, b"2", exptime=0)

    @pytest.mark.asyncio
    async def test_increment_missing_negative(self, memcached):
        memcached.client.decr.side_effect = aiomcache.exceptions.ClientException("NOT_FOUND")
        await memcached._increment(pytest.KEY, -2)
        memcached.client.decr.assert_called_with(pytest.KEY, 2)
        memcached.client.set.assert_called_with(pytest.KEY, b"-2", exptime=0)

    @pytest.mark.asyncio
    async def test_increment_typerror(self, memcached):
        memcached.client.incr.side_effect = aiomcache.exceptions.ClientException("")
        with pytest.raises(TypeError):
            await memcached._increment(pytest.KEY, 2)

    @pytest.mark.asyncio
    async def test_expire(self, memcached):
        await memcached._expire(pytest.KEY, 1)
        memcached.client.touch.assert_called_with(pytest.KEY, 1)

    @pytest.mark.asyncio
    async def test_delete(self, memcached):
        assert await memcached._delete(pytest.KEY) == 1
        memcached.client.delete.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_delete_missing(self, memcached):
        memcached.client.delete.return_value = False
        assert await memcached._delete(pytest.KEY) == 0
        memcached.client.delete.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_clear(self, memcached):
        await memcached._clear()
        memcached.client.flush_all.assert_called_with()

    @pytest.mark.asyncio
    async def test_clear_with_namespace(self, memcached):
        with pytest.raises(ValueError):
            await memcached._clear("nm")

    @pytest.mark.asyncio
    async def test_raw(self, memcached):
        await memcached._raw("get", pytest.KEY)
        memcached.client.get.assert_called_with(pytest.KEY)
