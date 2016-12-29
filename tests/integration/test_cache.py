import pytest
import asyncio
import random
import string

from marshmallow import fields, Schema, post_load

from aiocache import serializers, RedisCache


@pytest.fixture(params=[
    'redis_cache',
    'memory_cache',
    'memcached_cache',
])
def cache(request):
    return request.getfuncargvalue(request.param)


class MyType:
    MY_CONSTANT = "CONSTANT"

    def __init__(self, int_type=None, str_type=None, dict_type=None, list_type=None):
        self.int_type = int_type or random.randint(1, 10)
        self.str_type = str_type or random.choice(string.ascii_lowercase)
        self.dict_type = dict_type or {}
        self.list_type = list_type or []

    def __eq__(self, obj):
        return self.__dict__ == obj.__dict__


class MyTypeSchema(Schema):
    int_type = fields.Integer()
    str_type = fields.String()
    dict_type = fields.Dict()
    list_type = fields.List(fields.Integer())

    def dumps(self, *args, **kwargs):
        return super().dumps(*args, **kwargs).data

    def loads(self, *args, **kwargs):
        return super().loads(*args, **kwargs).data

    @post_load
    def build_my_type(self, data):
        return MyType(**data)

    class Meta:
        strict = True


def dumps(x):
    if x == "value":
        return "v4lu3"
    return 100


def loads(x):
    if x == "v4lu3":
        return "value"
    return 200


class TestCache:
    """
    This class ensures that all caches behave the same way and have the minimum functionality.
    To add a new cache just create the fixture for the new cache and add id as a param for the
    cache fixture
    """
    @pytest.mark.asyncio
    async def test_setup(self, cache):
        assert cache.namespace == "test"
        assert isinstance(cache.serializer, serializers.DefaultSerializer)

    @pytest.mark.asyncio
    async def test_get_missing(self, cache):
        assert await cache.get(pytest.KEY) is None
        assert await cache.get(pytest.KEY, default=1) == 1

    @pytest.mark.asyncio
    async def test_get_existing(self, cache):
        await cache.set(pytest.KEY, "value")
        assert await cache.get(pytest.KEY) == "value"

    @pytest.mark.asyncio
    async def test_multi_get(self, cache):
        await cache.set(pytest.KEY, "value")
        assert await cache.multi_get([pytest.KEY, pytest.KEY_1]) == ["value", None]

    @pytest.mark.asyncio
    async def test_delete_missing(self, cache):
        assert await cache.delete(pytest.KEY) == 0

    @pytest.mark.asyncio
    async def test_delete_existing(self, cache):
        await cache.set(pytest.KEY, "value")
        assert await cache.delete(pytest.KEY) == 1

        assert await cache.get(pytest.KEY) is None

    @pytest.mark.asyncio
    async def test_set(self, cache):
        assert await cache.set(pytest.KEY, "value") is True

    @pytest.mark.asyncio
    async def test_multi_set(self, cache):
        pairs = [(pytest.KEY, "value"), [pytest.KEY_1, "random_value"]]
        assert await cache.multi_set(pairs) is True
        assert await cache.multi_get([pytest.KEY, pytest.KEY_1]) == ["value", "random_value"]

    @pytest.mark.asyncio
    async def test_multi_set_with_ttl(self, cache):
        pairs = [(pytest.KEY, "value"), [pytest.KEY_1, "random_value"]]
        assert await cache.multi_set(pairs, ttl=1) is True
        await asyncio.sleep(1.1)

        assert await cache.multi_get([pytest.KEY, pytest.KEY_1]) == [None, None]

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache):
        await cache.set(pytest.KEY, "value", ttl=1)
        await asyncio.sleep(1.1)

        assert await cache.get(pytest.KEY) is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("obj, serializer", [
        (MyType().str_type, serializers.DefaultSerializer),
        (MyType(), serializers.PickleSerializer),
        (MyType().__dict__, serializers.JsonSerializer),
    ])
    async def test_set_complex_type(self, cache, obj, serializer):
        cache.serializer = serializer()
        assert await cache.set(pytest.KEY, obj) is True

    @pytest.mark.asyncio
    @pytest.mark.parametrize("obj, serializer", [
        (MyType().str_type, serializers.DefaultSerializer),
        (MyType(), serializers.PickleSerializer),
        (MyType().__dict__, serializers.JsonSerializer),
    ])
    async def test_get_complex_type(self, cache, obj, serializer):
        cache.serializer = serializer()
        await cache.set(pytest.KEY, obj)
        assert await cache.get(pytest.KEY) == obj

    @pytest.mark.asyncio
    async def test_get_set_alt_serializer_functions(self, cache):
        await cache.set(pytest.KEY, "value", dumps_fn=dumps)
        assert await cache.get(pytest.KEY) == "v4lu3"
        assert await cache.get(pytest.KEY, loads_fn=loads) == "value"

    @pytest.mark.asyncio
    async def test_get_set_alt_serializer_class(self, cache):
        my_serializer = MyTypeSchema()
        my_obj = MyType()
        cache.serializer = my_serializer
        await cache.set(pytest.KEY, my_obj)
        assert await cache.get(pytest.KEY) == my_serializer.loads(my_serializer.dumps(my_obj))

    @pytest.mark.asyncio
    async def test_add_missing(self, cache):
        assert await cache.add(pytest.KEY, "value", ttl=1) is True

    @pytest.mark.asyncio
    async def test_add_existing(self, cache):
        await cache.set(pytest.KEY, "value") is True
        with pytest.raises(ValueError):
            await cache.add(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_exists_missing(self, cache):
        assert await cache.exists(pytest.KEY) is False

    @pytest.mark.asyncio
    async def test_exists_existing(self, cache):
        await cache.set(pytest.KEY, "value")
        assert await cache.exists(pytest.KEY) is True

    @pytest.mark.asyncio
    async def test_expire_existing(self, cache):
        await cache.set(pytest.KEY, "value")
        assert await cache.expire(pytest.KEY, 1) is True
        await asyncio.sleep(1.1)
        assert await cache.exists(pytest.KEY) is False

    @pytest.mark.asyncio
    async def test_expire_missing(self, cache):
        assert await cache.expire(pytest.KEY, 1) is False

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        await cache.set(pytest.KEY, "value")
        await cache.clear()

        assert await cache.exists(pytest.KEY) is False

    @pytest.mark.asyncio
    async def test_clear_with_namespace_redis(self, redis_cache):
        await redis_cache.set(pytest.KEY, "value", namespace="test")
        await redis_cache.clear(namespace="test")

        assert await redis_cache.exists(pytest.KEY, namespace="test") is False

    @pytest.mark.asyncio
    async def test_clear_with_namespace_memory(self, memory_cache):
        await memory_cache.set(pytest.KEY, "value", namespace="test")
        await memory_cache.clear(namespace="test")

        assert await memory_cache.exists(pytest.KEY, namespace="test") is False

    @pytest.mark.asyncio
    async def test_clear_with_namespace_memcached(self, memcached_cache):
        await memcached_cache.set(pytest.KEY, "value", namespace="test")

        with pytest.raises(ValueError):
            await memcached_cache.clear(namespace="test")

        assert await memcached_cache.exists(pytest.KEY, namespace="test") is True


class TestMemoryCache:

    @pytest.mark.asyncio
    async def test_raw(self, memory_cache):
        await memory_cache.raw('setdefault', b"key", b"value")
        assert await memory_cache.raw("get", b"key") == b"value"
        assert list(await memory_cache.raw("keys")) == [b"key"]


class TestMemcachedCache:

    @pytest.mark.asyncio
    async def test_raw(self, memcached_cache):
        await memcached_cache.raw('set', b"key", b"value")
        assert await memcached_cache.raw("get", b"key") == b"value"
        assert await memcached_cache.raw("prepend", b"key", b"super") is True
        assert await memcached_cache.raw("get", b"key") == b"supervalue"


class TestRedisCache:
    @pytest.mark.asyncio
    async def test_raw(self, redis_cache):
        await redis_cache.raw('set', "key", "value")
        assert await redis_cache.raw("get", "key") == "value"
        assert await redis_cache.raw("keys", "k*") == ["key"]

    @pytest.mark.asyncio
    async def test_pool_reusage(self):
        cache = RedisCache()
        await cache._clear(None)

        other_cache = RedisCache()
        await other_cache._clear(None)

        assert len(RedisCache.pools) == 1

        cache.db = 1
        await cache._clear(None)

        assert len(RedisCache.pools) == 2
        assert other_cache.db == 0
