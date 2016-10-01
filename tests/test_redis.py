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
def redis_cache():
    cache = RedisCache(namespace="test")
    yield cache


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
        assert await redis_cache.get("key") is None
        assert await redis_cache.get("key", default=1) == 1

        await redis_cache.delete("key")

    @pytest.mark.asyncio
    async def test_get_existing(self, redis_cache):
        await redis_cache.set("key", "value")
        assert await redis_cache.get("key") == "value"

        await redis_cache.delete("key")

    @pytest.mark.asyncio
    async def test_delete_missing(self, redis_cache):
        assert await redis_cache.delete("key") == 0

    @pytest.mark.asyncio
    async def test_delete_existing(self, redis_cache):
        await redis_cache.set("key", "value")
        await redis_cache.delete("key")

        assert await redis_cache.get("key") is None

    @pytest.mark.asyncio
    async def test_set(self, redis_cache):
        assert await redis_cache.set("key", "value") is True

        await redis_cache.delete("key")

    @pytest.mark.asyncio
    async def test_set_with_timeout(self, redis_cache):
        await redis_cache.set("key", "value", timeout=1)
        await asyncio.sleep(2)

        assert await redis_cache.get("key") is None

    @pytest.mark.asyncio
    async def test_incr(self, redis_cache):
        assert await redis_cache.incr("key") == 1
        assert await redis_cache.incr("key", 1) == 2
        assert await redis_cache.incr("key", 5) == 7

        await redis_cache.delete("key")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("obj, serializer", [
        (MyType().str, DefaultSerializer),
        (MyType(), PickleSerializer),
        (MyType().__dict__, JsonSerializer),
    ])
    async def test_set_complex_type(self, redis_cache, obj, serializer):
        redis_cache.serializer = serializer()
        assert await redis_cache.set("key", obj) is True

        await redis_cache.delete("key")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("obj, serializer", [
        (MyType().str, DefaultSerializer),
        (MyType(), PickleSerializer),
        (MyType().__dict__, JsonSerializer),
    ])
    async def test_get_complex_type(self, redis_cache, obj, serializer):
        redis_cache.serializer = serializer()
        await redis_cache.set("key", obj)
        assert await redis_cache.get("key") == obj

        await redis_cache.delete("key")

    @pytest.mark.asyncio
    async def test_get_set_alt_serializer(self, redis_cache):
        await redis_cache.set("key", "value", serialize_fn=TestSerializer().serialize)
        assert await redis_cache.get("key") == "v4lu3"
        assert await redis_cache.get("key", deserialize_fn=TestSerializer().deserialize) == "value"

        await redis_cache.delete("key")

    @pytest.mark.asyncio
    async def test_ttl(self, redis_cache):
        await redis_cache.set("key", "value", timeout=10)
        assert await redis_cache.ttl("key") > 0

        await redis_cache.delete("key")
