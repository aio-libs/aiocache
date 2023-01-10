from unittest.mock import ANY, AsyncMock, create_autospec, patch

import pytest
from redis.asyncio.client import Pipeline
from redis.exceptions import ResponseError

from aiocache.backends.redis import RedisBackend, RedisCache
from aiocache.base import BaseCache, _ensure_key
from aiocache.serializers import JsonSerializer
from ...utils import Keys


@pytest.fixture
def redis():
    redis = RedisBackend()
    with patch.object(redis, "client", autospec=True) as m:
        # These methods actually return an awaitable.
        for method in (
            "eval", "expire", "get", "psetex", "setex", "execute_command", "exists",
            "incrby", "persist", "delete", "keys", "flushdb",
        ):
            setattr(m, method, AsyncMock(return_value=None, spec_set=()))
        m.mget = AsyncMock(return_value=[None], spec_set=())
        m.set = AsyncMock(return_value=True, spec_set=())

        m.pipeline.return_value = create_autospec(Pipeline, instance=True)
        m.pipeline.return_value.__aenter__.return_value = m.pipeline.return_value
        yield redis


class TestRedisBackend:
    default_redis_kwargs = {
        "host": "127.0.0.1",
        "port": 6379,
        "db": 0,
        "password": None,
        "socket_connect_timeout": None,
        "decode_responses": False,
        "max_connections": None,
    }

    @patch("redis.asyncio.Redis", name="mock_class", autospec=True)
    def test_setup(self, mock_class):
        redis_backend = RedisBackend()
        kwargs = self.default_redis_kwargs.copy()
        mock_class.assert_called_with(**kwargs)
        assert redis_backend.endpoint == "127.0.0.1"
        assert redis_backend.port == 6379
        assert redis_backend.db == 0
        assert redis_backend.password is None
        assert redis_backend.pool_max_size is None

    @patch("redis.asyncio.Redis", name="mock_class", autospec=True)
    def test_setup_override(self, mock_class):
        override = {"db": 2, "password": "pass"}
        redis_backend = RedisBackend(**override)

        kwargs = self.default_redis_kwargs.copy()
        kwargs.update(override)
        mock_class.assert_called_with(**kwargs)

        assert redis_backend.endpoint == "127.0.0.1"
        assert redis_backend.port == 6379
        assert redis_backend.db == 2
        assert redis_backend.password == "pass"

    @patch("redis.asyncio.Redis", name="mock_class", autospec=True)
    def test_setup_casts(self, mock_class):
        override = {
            "db": "2",
            "port": "6379",
            "pool_max_size": "10",
            "create_connection_timeout": "1.5",
        }
        redis_backend = RedisBackend(**override)

        kwargs = self.default_redis_kwargs.copy()
        kwargs.update({
            "db": 2,
            "port": 6379,
            "max_connections": 10,
            "socket_connect_timeout": 1.5,
        })
        mock_class.assert_called_with(**kwargs)

        assert redis_backend.db == 2
        assert redis_backend.port == 6379
        assert redis_backend.pool_max_size == 10
        assert redis_backend.create_connection_timeout == 1.5

    async def test_get(self, redis):
        redis.client.get.return_value = b"value"
        assert await redis._get(Keys.KEY) == "value"
        redis.client.get.assert_called_with(Keys.KEY)

    async def test_gets(self, mocker, redis):
        mocker.spy(redis, "_get")
        await redis._gets(Keys.KEY)
        redis._get.assert_called_with(Keys.KEY, encoding="utf-8", _conn=ANY)

    async def test_set(self, redis):
        await redis._set(Keys.KEY, "value")
        redis.client.set.assert_called_with(Keys.KEY, "value")

        await redis._set(Keys.KEY, "value", ttl=1)
        redis.client.setex.assert_called_with(Keys.KEY, 1, "value")

    async def test_set_cas_token(self, mocker, redis):
        mocker.spy(redis, "_cas")
        await redis._set(Keys.KEY, "value", _cas_token="old_value", _conn=redis.client)
        redis._cas.assert_called_with(
            Keys.KEY, "value", "old_value", ttl=None, _conn=redis.client
        )

    async def test_cas(self, mocker, redis):
        mocker.spy(redis, "_raw")
        await redis._cas(Keys.KEY, "value", "old_value", ttl=10, _conn=redis.client)
        redis._raw.assert_called_with(
            "eval",
            redis.CAS_SCRIPT,
            1,
            *[Keys.KEY, "value", "old_value", "EX", 10],
            _conn=redis.client,
        )

    async def test_cas_float_ttl(self, mocker, redis):
        mocker.spy(redis, "_raw")
        await redis._cas(Keys.KEY, "value", "old_value", ttl=0.1, _conn=redis.client)
        redis._raw.assert_called_with(
            "eval",
            redis.CAS_SCRIPT,
            1,
            *[Keys.KEY, "value", "old_value", "PX", 100],
            _conn=redis.client,
        )

    async def test_multi_get(self, redis):
        await redis._multi_get([Keys.KEY, Keys.KEY_1])
        redis.client.mget.assert_called_with(Keys.KEY, Keys.KEY_1)

    async def test_multi_set(self, redis):
        await redis._multi_set([(Keys.KEY, "value"), (Keys.KEY_1, "random")])
        redis.client.execute_command.assert_called_with(
            "MSET", Keys.KEY, "value", Keys.KEY_1, "random"
        )

    async def test_multi_set_with_ttl(self, redis):
        await redis._multi_set([(Keys.KEY, "value"), (Keys.KEY_1, "random")], ttl=1)
        assert redis.client.pipeline.call_count == 1
        pipeline = redis.client.pipeline.return_value
        pipeline.execute_command.assert_called_with(
            "MSET", Keys.KEY, "value", Keys.KEY_1, "random"
        )
        pipeline.expire.assert_any_call(Keys.KEY, time=1)
        pipeline.expire.assert_any_call(Keys.KEY_1, time=1)
        assert pipeline.execute.call_count == 1

    async def test_add(self, redis):
        await redis._add(Keys.KEY, "value")
        redis.client.set.assert_called_with(Keys.KEY, "value", nx=True, ex=None)

        await redis._add(Keys.KEY, "value", 1)
        redis.client.set.assert_called_with(Keys.KEY, "value", nx=True, ex=1)

    async def test_add_existing(self, redis):
        redis.client.set.return_value = False
        with pytest.raises(ValueError):
            await redis._add(Keys.KEY, "value")

    async def test_add_float_ttl(self, redis):
        await redis._add(Keys.KEY, "value", 0.1)
        redis.client.set.assert_called_with(Keys.KEY, "value", nx=True, px=100)

    async def test_exists(self, redis):
        redis.client.exists.return_value = 1
        await redis._exists(Keys.KEY)
        redis.client.exists.assert_called_with(Keys.KEY)

    async def test_increment(self, redis):
        await redis._increment(Keys.KEY, delta=2)
        redis.client.incrby.assert_called_with(Keys.KEY, 2)

    async def test_increment_typerror(self, redis):
        redis.client.incrby.side_effect = ResponseError("msg")
        with pytest.raises(TypeError):
            await redis._increment(Keys.KEY, delta=2)
        redis.client.incrby.assert_called_with(Keys.KEY, 2)

    async def test_expire(self, redis):
        await redis._expire(Keys.KEY, 1)
        redis.client.expire.assert_called_with(Keys.KEY, 1)
        await redis._increment(Keys.KEY, 2)

    async def test_expire_0_ttl(self, redis):
        await redis._expire(Keys.KEY, ttl=0)
        redis.client.persist.assert_called_with(Keys.KEY)

    async def test_delete(self, redis):
        await redis._delete(Keys.KEY)
        redis.client.delete.assert_called_with(Keys.KEY)

    async def test_clear(self, redis):
        redis.client.keys.return_value = ["nm:a", "nm:b"]
        await redis._clear("nm")
        redis.client.delete.assert_called_with("nm:a", "nm:b")

    async def test_clear_no_keys(self, redis):
        redis.client.keys.return_value = []
        await redis._clear("nm")
        redis.client.delete.assert_not_called()

    async def test_clear_no_namespace(self, redis):
        await redis._clear()
        assert redis.client.flushdb.call_count == 1

    async def test_raw(self, redis):
        await redis._raw("get", Keys.KEY)
        await redis._raw("set", Keys.KEY, 1)
        redis.client.get.assert_called_with(Keys.KEY)
        redis.client.set.assert_called_with(Keys.KEY, 1)

    async def test_redlock_release(self, mocker, redis):
        mocker.spy(redis, "_raw")
        await redis._redlock_release(Keys.KEY, "random")
        redis._raw.assert_called_with("eval", redis.RELEASE_SCRIPT, 1, Keys.KEY, "random")

    async def test_close(self, redis):
        await redis._close()
        assert redis.client.close.call_count == 1


class TestRedisCache:
    @pytest.fixture
    def set_test_namespace(self, redis_cache):
        redis_cache.namespace = "test"
        yield
        redis_cache.namespace = None

    def test_name(self):
        assert RedisCache.NAME == "redis"

    def test_inheritance(self):
        assert isinstance(RedisCache(), BaseCache)

    def test_default_serializer(self):
        assert isinstance(RedisCache().serializer, JsonSerializer)

    @pytest.mark.parametrize(
        "path,expected", [("", {}), ("/", {}), ("/1", {"db": "1"}), ("/1/2/3", {"db": "1"})]
    )
    def test_parse_uri_path(self, path, expected):
        assert RedisCache().parse_uri_path(path) == expected

    @pytest.mark.parametrize(
        "namespace, expected",
        ([None, "test:" + _ensure_key(Keys.KEY)], ["", _ensure_key(Keys.KEY)], ["my_ns", "my_ns:" + _ensure_key(Keys.KEY)]),  # noqa: B950
    )
    def test_build_key_double_dot(self, set_test_namespace, redis_cache, namespace, expected):
        assert redis_cache.build_key(Keys.KEY, namespace=namespace) == expected

    def test_build_key_no_namespace(self, redis_cache):
        assert redis_cache.build_key(Keys.KEY, namespace=None) == Keys.KEY
