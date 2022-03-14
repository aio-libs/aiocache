import pickle
import random

import pytest
from marshmallow import Schema, fields, post_load

try:
    import ujson as json
except ImportError:
    import json  # type: ignore[no-redef]

from aiocache.serializers import (
    BaseSerializer,
    JsonSerializer,
    NullSerializer,
    PickleSerializer,
    StringSerializer,
)


class MyType:
    MY_CONSTANT = "CONSTANT"

    def __init__(self, r=None):
        self.r = r or random.randint(1, 10)

    def __eq__(self, obj):
        return self.__dict__ == obj.__dict__


class MyTypeSchema(Schema, BaseSerializer):
    r = fields.Integer()
    encoding = "utf-8"

    def dumps(self, *args, **kwargs):
        return super().dumps(*args, **kwargs)

    def loads(self, *args, **kwargs):
        return super().loads(*args, **kwargs)

    @post_load
    def build_my_type(self, data, **kwargs):
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


class TestNullSerializer:

    TYPES = [1, 2.0, "hi", True, ["1", 1], {"key": "value"}, MyType()]

    @pytest.mark.parametrize("obj", TYPES)
    @pytest.mark.asyncio
    async def test_set_get_types(self, memory_cache, obj):
        memory_cache.serializer = NullSerializer()
        assert await memory_cache.set(pytest.KEY, obj) is True
        assert await memory_cache.get(pytest.KEY) is obj

    @pytest.mark.parametrize("obj", TYPES)
    @pytest.mark.asyncio
    async def test_add_get_types(self, memory_cache, obj):
        memory_cache.serializer = NullSerializer()
        assert await memory_cache.add(pytest.KEY, obj) is True
        assert await memory_cache.get(pytest.KEY) is obj

    @pytest.mark.parametrize("obj", TYPES)
    @pytest.mark.asyncio
    async def test_multi_set_multi_get_types(self, memory_cache, obj):
        memory_cache.serializer = NullSerializer()
        assert await memory_cache.multi_set([(pytest.KEY, obj)]) is True
        assert (await memory_cache.multi_get([pytest.KEY]))[0] is obj


class TestStringSerializer:

    TYPES = [1, 2.0, "hi", True, ["1", 1], {"key": "value"}, MyType()]

    @pytest.mark.parametrize("obj", TYPES)
    @pytest.mark.asyncio
    async def test_set_get_types(self, cache, obj):
        cache.serializer = StringSerializer()
        assert await cache.set(pytest.KEY, obj) is True
        assert await cache.get(pytest.KEY) == str(obj)

    @pytest.mark.parametrize("obj", TYPES)
    @pytest.mark.asyncio
    async def test_add_get_types(self, cache, obj):
        cache.serializer = StringSerializer()
        assert await cache.add(pytest.KEY, obj) is True
        assert await cache.get(pytest.KEY) == str(obj)

    @pytest.mark.parametrize("obj", TYPES)
    @pytest.mark.asyncio
    async def test_multi_set_multi_get_types(self, cache, obj):
        cache.serializer = StringSerializer()
        assert await cache.multi_set([(pytest.KEY, obj)]) is True
        assert await cache.multi_get([pytest.KEY]) == [str(obj)]


class TestJsonSerializer:

    TYPES = [1, 2.0, "hi", True, ["1", 1], {"key": "value"}]

    @pytest.mark.parametrize("obj", TYPES)
    @pytest.mark.asyncio
    async def test_set_get_types(self, cache, obj):
        cache.serializer = JsonSerializer()
        assert await cache.set(pytest.KEY, obj) is True
        assert await cache.get(pytest.KEY) == json.loads(json.dumps(obj))

    @pytest.mark.parametrize("obj", TYPES)
    @pytest.mark.asyncio
    async def test_add_get_types(self, cache, obj):
        cache.serializer = JsonSerializer()
        assert await cache.add(pytest.KEY, obj) is True
        assert await cache.get(pytest.KEY) == json.loads(json.dumps(obj))

    @pytest.mark.parametrize("obj", TYPES)
    @pytest.mark.asyncio
    async def test_multi_set_multi_get_types(self, cache, obj):
        cache.serializer = JsonSerializer()
        assert await cache.multi_set([(pytest.KEY, obj)]) is True
        assert await cache.multi_get([pytest.KEY]) == [json.loads(json.dumps(obj))]


class TestPickleSerializer:

    TYPES = [1, 2.0, "hi", True, ["1", 1], {"key": "value"}, MyType()]

    @pytest.mark.parametrize("obj", TYPES)
    @pytest.mark.asyncio
    async def test_set_get_types(self, cache, obj):
        cache.serializer = PickleSerializer()
        assert await cache.set(pytest.KEY, obj) is True
        assert await cache.get(pytest.KEY) == pickle.loads(pickle.dumps(obj))

    @pytest.mark.parametrize("obj", TYPES)
    @pytest.mark.asyncio
    async def test_add_get_types(self, cache, obj):
        cache.serializer = PickleSerializer()
        assert await cache.add(pytest.KEY, obj) is True
        assert await cache.get(pytest.KEY) == pickle.loads(pickle.dumps(obj))

    @pytest.mark.parametrize("obj", TYPES)
    @pytest.mark.asyncio
    async def test_multi_set_multi_get_types(self, cache, obj):
        cache.serializer = PickleSerializer()
        assert await cache.multi_set([(pytest.KEY, obj)]) is True
        assert await cache.multi_get([pytest.KEY]) == [pickle.loads(pickle.dumps(obj))]


class TestAltSerializers:
    @pytest.mark.asyncio
    async def test_get_set_alt_serializer_functions(self, cache):
        cache.serializer = StringSerializer()
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
