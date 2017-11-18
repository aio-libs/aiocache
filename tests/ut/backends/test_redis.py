import pytest
import aioredis

from asynctest import CoroutineMock, MagicMock, patch, ANY

from aiocache import RedisCache
from aiocache.base import BaseCache
from aiocache.serializers import JsonSerializer
from aiocache.backends.redis import RedisBackend, conn, AIOREDIS_BEFORE_ONE


class FakeRedisConn:

    SET_IF_NOT_EXIST = 'SET_IF_NOT_EXIST'

    def __init__(self):
        self.get = CoroutineMock()
        self.mget = CoroutineMock()
        self.set = CoroutineMock()
        self.setex = CoroutineMock()
        self.mset = CoroutineMock()
        self.incrby = CoroutineMock()
        self.exists = CoroutineMock()
        self.persist = CoroutineMock()
        self.expire = CoroutineMock()
        self.delete = CoroutineMock()
        self.flushdb = CoroutineMock()
        self.eval = CoroutineMock()
        self.keys = CoroutineMock()


class FakePool:

    SET_IF_NOT_EXIST = 'SET_IF_NOT_EXIST'

    def __init__(self):
        self.conn = FakeRedisConn()
        self.transaction = MagicMock()
        self.release = CoroutineMock()
        self.conn.multi_exec = MagicMock(return_value=self.transaction)
        self.conn.multi_exec.return_value.execute = CoroutineMock()
        self.clear = CoroutineMock()
        self._pool_or_conn = self

    def __await__(self):
        yield
        return self

    async def acquire(self):
        return self.conn

    def __enter__(self):
        return self.conn

    def __exit__(self, *args, **kwargs):
        pass

    def __call__(self):
        return self

    def __getattr__(self, name):
        if AIOREDIS_BEFORE_ONE:
            return super().__getattr__(name)

        return getattr(self.conn, name)


@pytest.fixture
def create_pool():
    if AIOREDIS_BEFORE_ONE:
        with patch(
                "aiocache.backends.redis.aioredis.create_pool") as create_pool:
            yield create_pool
    else:
        with patch(
                "aiocache.backends.redis.aioredis.create_redis_pool") as create_pool:
            yield create_pool


@pytest.fixture
def redis():
    redis = RedisBackend()
    pool = FakePool()
    redis._connect = pool
    yield redis, pool


class TestRedisBackend:

    def test_setup(self):
        redis_backend = RedisBackend()
        assert redis_backend.endpoint == "127.0.0.1"
        assert redis_backend.port == 6379
        assert redis_backend.db == 0
        assert redis_backend.password is None
        assert redis_backend.pool_min_size == 1
        assert redis_backend.pool_max_size == 10

    def test_setup_override(self):
        redis_backend = RedisBackend(
            db=2,
            password="pass")

        assert redis_backend.endpoint == "127.0.0.1"
        assert redis_backend.port == 6379
        assert redis_backend.db == 2
        assert redis_backend.password == "pass"

    @pytest.mark.asyncio
    async def test_acquire_conn(self):
        redis = RedisBackend()
        pool = FakePool()
        redis._pool = pool
        if AIOREDIS_BEFORE_ONE:
            assert await redis.acquire_conn() == pool.conn
        else:
            assert await redis.acquire_conn() == pool

    @pytest.mark.asyncio
    async def test_release_conn(self):
        redis = RedisBackend()
        pool = FakePool()
        redis._pool = pool
        conn = await redis.acquire_conn()
        await redis.release_conn(conn)
        redis._pool.release.assert_called_with(conn)

    @pytest.mark.asyncio
    async def test_connect_with_pool(self, redis, create_pool):
        _, pool = redis
        create_pool.return_value = pool
        redis = RedisBackend()
        assert await redis._connect() == pool
        assert create_pool.call_count == 1

    @pytest.mark.asyncio
    async def test_connect_locked(self, mocker, create_pool):
        redis = RedisBackend()
        pool = FakePool()
        create_pool.return_value = pool
        mocker.spy(redis._pool_lock, "acquire")
        mocker.spy(redis._pool_lock, "release")

        assert await redis._connect() == pool
        assert redis._pool_lock.acquire.call_count == 1
        assert redis._pool_lock.release.call_count == 1

    @pytest.mark.asyncio
    async def test_connect_calls_create_pool(self, create_pool):
        pool = FakePool()
        create_pool.return_value = pool
        redis = RedisBackend()
        await redis._connect()
        create_pool.assert_called_with(
            (redis.endpoint, redis.port),
            db=redis.db,
            password=redis.password,
            loop=redis._loop,
            encoding="utf-8",
            minsize=redis.pool_min_size,
            maxsize=redis.pool_max_size)

    @pytest.mark.asyncio
    async def test_connect_sets_pool(self, create_pool):
        pool = FakePool()
        create_pool.return_value = pool
        redis = RedisBackend()
        await redis._connect()
        assert redis._pool == pool

    @pytest.mark.asyncio
    async def test_connect_reuses_existing_pool(self, redis):
        cache, pool = redis
        cache._pool = pool
        await cache._connect()
        assert cache._pool == pool

    @pytest.mark.asyncio
    async def test_get(self, redis):
        cache, pool = redis
        await cache._get(pytest.KEY)
        pool.conn.get.assert_called_with(pytest.KEY, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_gets(self, mocker, redis):
        cache, pool = redis
        mocker.spy(cache, '_get')
        await cache._gets(pytest.KEY)
        cache._get.assert_called_with(pytest.KEY, encoding="utf-8", _conn=ANY)

    @pytest.mark.asyncio
    async def test_set(self, redis):
        cache, pool = redis
        await cache._set(pytest.KEY, "value")
        pool.conn.set.assert_called_with(pytest.KEY, "value")

        await cache._set(pytest.KEY, "value", ttl=1)
        pool.conn.setex.assert_called_with(pytest.KEY, 1, "value")

    @pytest.mark.asyncio
    async def test_set_cas_token(self, mocker, redis):
        cache, pool = redis
        mocker.spy(cache, '_cas')
        await cache._set(pytest.KEY, 'value', _cas_token='old_value', _conn=pool.conn)
        cache._cas.assert_called_with(
            pytest.KEY, 'value', 'old_value', ttl=None, _conn=pool.conn)

    @pytest.mark.asyncio
    async def test_cas(self, mocker, redis):
        cache, pool = redis
        mocker.spy(cache, '_raw')
        await cache._cas(pytest.KEY, 'value', 'old_value', ttl=10, _conn=pool.conn)
        cache._raw.assert_called_with(
            'eval', cache.CAS_SCRIPT,
            [pytest.KEY], ['value', 'old_value', 'EX', 10], _conn=pool.conn)

    @pytest.mark.asyncio
    async def test_cas_float_ttl(self, mocker, redis):
        cache, pool = redis
        mocker.spy(cache, '_raw')
        await cache._cas(pytest.KEY, 'value', 'old_value', ttl=0.1, _conn=pool.conn)
        cache._raw.assert_called_with(
            'eval', cache.CAS_SCRIPT,
            [pytest.KEY], ['value', 'old_value', 'PX', 100], _conn=pool.conn)

    @pytest.mark.asyncio
    async def test_multi_get(self, redis):
        cache, pool = redis
        await cache._multi_get([pytest.KEY, pytest.KEY_1])
        pool.conn.mget.assert_called_with(pytest.KEY, pytest.KEY_1, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_multi_set(self, redis):
        cache, pool = redis
        await cache._multi_set([(pytest.KEY, "value"), (pytest.KEY_1, "random")])
        pool.conn.mset.assert_called_with(pytest.KEY, "value", pytest.KEY_1, "random")

    @pytest.mark.asyncio
    async def test_multi_set_with_ttl(self, redis):
        cache, pool = redis
        await cache._multi_set([(pytest.KEY, "value"), (pytest.KEY_1, "random")], ttl=1)
        assert pool.conn.multi_exec.call_count == 1
        pool.transaction.mset.assert_called_with(pytest.KEY, "value", pytest.KEY_1, "random")
        pool.transaction.expire.assert_any_call(pytest.KEY, timeout=1)
        pool.transaction.expire.assert_any_call(pytest.KEY_1, timeout=1)
        assert pool.transaction.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_add(self, redis):
        cache, pool = redis
        await cache._add(pytest.KEY, "value")
        pool.conn.set.assert_called_with(
            pytest.KEY, "value", exist=pool.SET_IF_NOT_EXIST, expire=None)

        await cache._add(pytest.KEY, "value", 1)
        pool.conn.set.assert_called_with(
            pytest.KEY, "value", exist=pool.SET_IF_NOT_EXIST, expire=1)

    @pytest.mark.asyncio
    async def test_add_existing(self, redis):
        cache, pool = redis
        pool.conn.set.return_value = False
        with pytest.raises(ValueError):
            await cache._add(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_add_float_ttl(self, redis):
        cache, pool = redis
        await cache._add(pytest.KEY, "value", 0.1)
        pool.conn.set.assert_called_with(
            pytest.KEY, "value", exist=pool.SET_IF_NOT_EXIST, pexpire=100)

    @pytest.mark.asyncio
    async def test_exists(self, redis):
        cache, pool = redis
        pool.conn.exists.return_value = 1
        await cache._exists(pytest.KEY)
        pool.conn.exists.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_expire(self, redis):
        cache, pool = redis
        await cache._expire(pytest.KEY, ttl=1)
        pool.conn.expire.assert_called_with(pytest.KEY, 1)

    @pytest.mark.asyncio
    async def test_increment(self, redis):
        cache, pool = redis
        await cache._increment(pytest.KEY, delta=2)
        pool.conn.incrby.assert_called_with(pytest.KEY, 2)

    @pytest.mark.asyncio
    async def test_increment_typerror(self, redis):
        cache, pool = redis
        if AIOREDIS_BEFORE_ONE:
            pool.conn.incrby.side_effect = aioredis.errors.ReplyError
        else:
            pool.incrby.side_effect = aioredis.errors.ReplyError('msg')
        with pytest.raises(TypeError):
            await cache._increment(pytest.KEY, 2)

    @pytest.mark.asyncio
    async def test_expire_0_ttl(self, redis):
        cache, pool = redis
        await cache._expire(pytest.KEY, ttl=0)
        pool.conn.persist.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_delete(self, redis):
        cache, pool = redis
        await cache._delete(pytest.KEY)
        pool.conn.delete.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_clear(self, redis):
        cache, pool = redis
        pool.conn.keys.return_value = ["nm:a", "nm:b"]
        await cache._clear("nm")
        pool.conn.delete.assert_called_with("nm:a", "nm:b")

    @pytest.mark.asyncio
    async def test_clear_no_namespace(self, redis):
        cache, pool = redis
        await cache._clear()
        assert pool.conn.flushdb.call_count == 1

    @pytest.mark.asyncio
    async def test_raw(self, redis):
        cache, pool = redis
        await cache._raw("get", pytest.KEY)
        await cache._raw("set", pytest.KEY, 1)
        pool.conn.get.assert_called_with(pytest.KEY, encoding=ANY)
        pool.conn.set.assert_called_with(pytest.KEY, 1)

    @pytest.mark.asyncio
    async def test_redlock_release(self, mocker, redis):
        cache, pool = redis
        mocker.spy(cache, "_raw")
        await cache._redlock_release(pytest.KEY, "random")
        cache._raw.assert_called_with(
            "eval", cache.RELEASE_SCRIPT,
            [pytest.KEY], ["random"])

    @pytest.mark.asyncio
    async def test_close_when_connected(self, redis):
        cache, pool = redis
        cache._pool = pool
        await cache._raw("set", pytest.KEY, 1)
        await cache._close()
        if AIOREDIS_BEFORE_ONE:
            assert pool.clear.call_count == 1

    @pytest.mark.asyncio
    async def test_close_when_not_connected(self, redis):
        cache, pool = redis
        await cache._close()
        assert pool.clear.call_count == 0


class TestConn:

    async def dummy(self, *args, _conn=None, **kwargs):
        pass

    @pytest.mark.asyncio
    async def test_conn(self, redis, mocker):
        mocker.spy(self, "dummy")
        cache, pool = redis
        cache._pool = pool
        d = conn(self.dummy)
        await d(cache, "a", _conn=None)
        if AIOREDIS_BEFORE_ONE:
            self.dummy.assert_called_with(cache, "a", _conn=pool.conn)
            pool.conn = "another_connection"
            await d(cache, "a", _conn=None)
            self.dummy.assert_called_with(cache, "a", _conn="another_connection")
        else:
            self.dummy.assert_called_with(cache, "a", _conn=pool)

    @pytest.mark.asyncio
    async def test_conn_reuses(self, redis, mocker):
        mocker.spy(self, "dummy")
        cache, pool = redis
        cache._pool = pool
        d = conn(self.dummy)
        first_conn = pool.conn
        await d(cache, "a", _conn=first_conn)
        self.dummy.assert_called_with(cache, "a", _conn=first_conn)
        pool.conn = "another_connection"
        await d(cache, "a", _conn=first_conn)
        self.dummy.assert_called_with(cache, "a", _conn=first_conn)


class TestRedisCache:

    @pytest.fixture
    def set_test_namespace(self, redis_cache):
        redis_cache.namespace = "test"
        yield
        redis_cache.namespace = None

    def test_inheritance(self):
        assert isinstance(RedisCache(), BaseCache)

    def test_default_serializer(self):
        assert isinstance(RedisCache().serializer, JsonSerializer)

    @pytest.mark.parametrize("namespace, expected", (
        [None, "test:" + pytest.KEY],
        ["", pytest.KEY],
        ["my_ns", "my_ns:" + pytest.KEY],)
    )
    def test_build_key_double_dot(self, set_test_namespace, redis_cache, namespace, expected):
        assert redis_cache.build_key(pytest.KEY, namespace=namespace) == expected

    def test_build_key_no_namespace(self, redis_cache):
        assert redis_cache.build_key(pytest.KEY, namespace=None) == pytest.KEY
