import asyncio
import pytest
import random
import string

from aiocache import RedisCache
from aiocache.serializers import DefaultSerializer, PickleSerializer, JsonSerializer


class MyType:
    """
    Class used to check the storage and retrieval of raw objects
    """
    MY_CONSTANT = "CONSTANT"

    def __init__(self):
        self.int = random.randint(1, 10)
        self.str = random.choice(string.ascii_lowercase)
        self.dict = {}
        self.list = []

    def __eq__(self, obj):
        return self.__dict__ == obj.__dict__


class TestSerializer:
    def serialize(self, x):
        if x == "value":
            return "v4lu3"
        return 100

    def deserialize(self, x):
        if x == "v4lu3":
            return "value"
        return 200


@pytest.fixture
def redis_cache(event_loop, mocker):
    cache = RedisCache(namespace="test", loop=event_loop)
    yield cache
    event_loop.run_until_complete(cache.delete(KEY))
    event_loop.run_until_complete(cache.delete("random"))
    cache._pool.close()
    event_loop.run_until_complete(cache._pool.wait_closed())


KEY = "key"


class TestRedisCache:

    def test_setup(self, redis_cache):
        assert redis_cache.endpoint == "127.0.0.1"
        assert redis_cache.port == 6379
        assert redis_cache.namespace == "test"
        assert isinstance(redis_cache.serializer, DefaultSerializer)

    def test_setup_override(self):
        redis_cache = RedisCache(serializer=JsonSerializer())
        assert redis_cache.endpoint == "127.0.0.1"
        assert redis_cache.port == 6379
        assert isinstance(redis_cache.serializer, JsonSerializer)

    @pytest.mark.asyncio
    async def test_get_missing(self, redis_cache):
        assert await redis_cache.get(KEY) is None
        assert await redis_cache.get(KEY, default=1) == 1

    @pytest.mark.asyncio
    async def test_get_existing(self, redis_cache):
        await redis_cache.set(KEY, "value")
        assert await redis_cache.get(KEY) == "value"

    @pytest.mark.asyncio
    async def test_multi_get(self, redis_cache):
        await redis_cache.set(KEY, "value")
        assert await redis_cache.multi_get([KEY, "random"]) == ["value", None]

    @pytest.mark.asyncio
    async def test_delete_missing(self, redis_cache):
        assert await redis_cache.delete(KEY) == 0

    @pytest.mark.asyncio
    async def test_delete_existing(self, redis_cache):
        await redis_cache.set(KEY, "value")
        await redis_cache.delete(KEY)

        assert await redis_cache.get(KEY) is None

    @pytest.mark.asyncio
    async def test_set(self, redis_cache):
        assert await redis_cache.set(KEY, "value") is True

    @pytest.mark.asyncio
    async def test_multi_set(self, redis_cache):
        pairs = [(KEY, "value"), ["random", "random_value"]]
        assert await redis_cache.multi_set(pairs) is True
        assert await redis_cache.multi_get([KEY, "random"]) == ["value", "random_value"]

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, redis_cache):
        await redis_cache.set(KEY, "value", ttl=1)
        await asyncio.sleep(2)

        assert await redis_cache.get(KEY) is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("obj, serializer", [
        (MyType().str, DefaultSerializer),
        (MyType(), PickleSerializer),
        (MyType().__dict__, JsonSerializer),
    ])
    async def test_set_complex_type(self, redis_cache, obj, serializer):
        redis_cache.serializer = serializer()
        assert await redis_cache.set(KEY, obj) is True

    @pytest.mark.asyncio
    @pytest.mark.parametrize("obj, serializer", [
        (MyType().str, DefaultSerializer),
        (MyType(), PickleSerializer),
        (MyType().__dict__, JsonSerializer),
    ])
    async def test_get_complex_type(self, redis_cache, obj, serializer):
        redis_cache.serializer = serializer()
        await redis_cache.set(KEY, obj)
        assert await redis_cache.get(KEY) == obj

    @pytest.mark.asyncio
    async def test_get_set_alt_serializer(self, redis_cache):
        await redis_cache.set(KEY, "value", serialize_fn=TestSerializer().serialize)
        assert await redis_cache.get(KEY) == "v4lu3"
        assert await redis_cache.get(KEY, deserialize_fn=TestSerializer().deserialize) == "value"

    @pytest.mark.asyncio
    async def test_ttl(self, redis_cache):
        await redis_cache.set(KEY, "value", ttl=10)
        assert await redis_cache.ttl(KEY) > 0
