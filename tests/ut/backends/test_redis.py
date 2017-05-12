import pytest
import aioredis

from asynctest import CoroutineMock, MagicMock, patch, ANY

from aiocache.backends.redis import RedisBackend


class FakePool:

    SET_IF_NOT_EXIST = 'SET_IF_NOT_EXIST'

    def __init__(self):
        client = CoroutineMock()
        client.SET_IF_NOT_EXIST = self.SET_IF_NOT_EXIST
        self.client = client
        self.transaction = MagicMock()
        self.client.multi_exec = MagicMock(return_value=self.transaction)
        self.client.multi_exec.return_value.execute = CoroutineMock()

    def __await__(self):
        yield
        return self

    def __enter__(self):
        return self.client

    def __exit__(self, *args, **kwargs):
        pass

    def __call__(self):
        return self


@pytest.fixture
def redis(event_loop):
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
    async def test_connect_with_pool(self):
        redis = RedisBackend()
        pool = FakePool()
        with patch(
                "aiocache.backends.redis.aioredis.create_pool",
                MagicMock(return_value=pool)):
            assert await redis._connect() == pool

    @pytest.mark.asyncio
    async def test_connect_locked(self, mocker):
        redis = RedisBackend()
        pool = FakePool()
        mocker.spy(redis._lock, "acquire")
        mocker.spy(redis._lock, "release")

        with patch(
                "aiocache.backends.redis.aioredis.create_pool",
                MagicMock(return_value=pool)):
            assert await redis._connect() == pool
            assert redis._lock.acquire.call_count == 1
            assert redis._lock.release.call_count == 1

    @pytest.mark.asyncio
    async def test_connect_calls_create_pool(self):
        with patch("aiocache.backends.redis.aioredis.create_pool") as create_pool:
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
    async def test_connect_sets_pool(self):
        with patch("aiocache.backends.redis.aioredis.create_pool") as create_pool:
            pool = FakePool()
            create_pool.return_value = pool
            redis = RedisBackend()
            await redis._connect()
        assert redis._pool == pool

    @pytest.mark.asyncio
    async def test_connect_reuses_existing_pool(self):
        pool = FakePool()
        redis = RedisBackend()
        redis._pool = pool
        await redis._connect()
        assert redis._pool == pool

    @pytest.mark.asyncio
    async def test_get(self, redis):
        cache, pool = redis
        await cache._get(pytest.KEY)
        pool.client.get.assert_called_with(pytest.KEY, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_set(self, redis):
        cache, pool = redis
        await cache._set(pytest.KEY, "value")
        pool.client.set.assert_called_with(pytest.KEY, "value", expire=None)

        await cache._set(pytest.KEY, "value", ttl=1)
        pool.client.set.assert_called_with(pytest.KEY, "value", expire=1)

    @pytest.mark.asyncio
    async def test_multi_get(self, redis):
        cache, pool = redis
        await cache._multi_get([pytest.KEY, pytest.KEY_1])
        pool.client.mget.assert_called_with(pytest.KEY, pytest.KEY_1, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_multi_set(self, redis):
        cache, pool = redis
        await cache._multi_set([(pytest.KEY, "value"), (pytest.KEY_1, "random")])
        assert pool.client.multi_exec.call_count == 1
        pool.transaction.mset.assert_called_with(pytest.KEY, "value", pytest.KEY_1, "random")
        assert pool.transaction.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_multi_set_with_ttl(self, redis):
        cache, pool = redis
        await cache._multi_set([(pytest.KEY, "value"), (pytest.KEY_1, "random")], ttl=1)
        assert pool.client.multi_exec.call_count == 1
        pool.transaction.mset.assert_called_with(pytest.KEY, "value", pytest.KEY_1, "random")
        pool.transaction.expire.assert_any_call(pytest.KEY, timeout=1)
        pool.transaction.expire.assert_any_call(pytest.KEY_1, timeout=1)
        assert pool.transaction.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_add(self, redis):
        cache, pool = redis
        await cache._add(pytest.KEY, "value")
        pool.client.set.assert_called_with(
            pytest.KEY, "value", expire=None, exist=pool.SET_IF_NOT_EXIST)

    @pytest.mark.asyncio
    async def test_add_existing(self, redis):
        cache, pool = redis
        pool.client.set.return_value = False
        with pytest.raises(ValueError):
            await cache._add(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_exists(self, redis):
        cache, pool = redis
        pool.client.exists.return_value = 1
        await cache._exists(pytest.KEY)
        pool.client.exists.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_expire(self, redis):
        cache, pool = redis
        await cache._expire(pytest.KEY, ttl=1)
        pool.client.expire.assert_called_with(pytest.KEY, 1)

    @pytest.mark.asyncio
    async def test_increment(self, redis):
        cache, pool = redis
        await cache._increment(pytest.KEY, delta=2)
        pool.client.incrby.assert_called_with(pytest.KEY, 2)

    @pytest.mark.asyncio
    async def test_increment_typerror(self, redis):
        cache, pool = redis
        pool.client.incrby.side_effect = aioredis.errors.ReplyError
        with pytest.raises(TypeError):
            await cache._increment(pytest.KEY, 2)

    @pytest.mark.asyncio
    async def test_expire_0_ttl(self, redis):
        cache, pool = redis
        await cache._expire(pytest.KEY, ttl=0)
        pool.client.persist.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_delete(self, redis):
        cache, pool = redis
        await cache._delete(pytest.KEY)
        pool.client.delete.assert_called_with(pytest.KEY)

    @pytest.mark.asyncio
    async def test_clear(self, redis):
        cache, pool = redis
        pool.client.keys.return_value = ["nm:a", "nm:b"]
        await cache._clear("nm")
        pool.client.delete.assert_called_with("nm:a", "nm:b")

    @pytest.mark.asyncio
    async def test_clear_no_namespace(self, redis):
        cache, pool = redis
        await cache._clear()
        assert pool.client.flushdb.call_count == 1

    @pytest.mark.asyncio
    async def test_raw(self, redis):
        cache, pool = redis
        await cache._raw("get", pytest.KEY)
        await cache._raw("set", pytest.KEY, 1)
        pool.client.get.assert_called_with(pytest.KEY, encoding=ANY)
        pool.client.set.assert_called_with(pytest.KEY, 1)
