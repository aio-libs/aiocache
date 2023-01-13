import pickle
import random
from typing import Any

import pytest
from marshmallow import Schema, fields, post_load

try:
    import ujson as json  # noqa: I900
except ImportError:
    import json  # type: ignore[no-redef]

from aiocache.serializers import (
    BaseSerializer,
    JsonSerializer,
    NullSerializer,
    PickleSerializer,
    StringSerializer,
)
from ..utils import Keys


class MyType:
    MY_CONSTANT = "CONSTANT"

    def __init__(self, r=None):
        self.r = r or random.randint(1, 10)

    def __eq__(self, obj):
        return self.__dict__ == obj.__dict__


class MySchema(Schema):
    r = fields.Integer()

    @post_load
    def build_my_type(self, data, **kwargs):
        return MyType(**data)

    class Meta:
        strict = True


class MyTypeSchema(BaseSerializer):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.schema = MySchema()

    def dumps(self, value: Any) -> str:
        return self.schema.dumps(value)

    def loads(self, value: str) -> Any:
        return self.schema.loads(value)


class TestNullSerializer:
    TYPES = (1, 2.0, "hi", True, ["1", 1], {"key": "value"}, MyType())

    @pytest.mark.parametrize("obj", TYPES)
    async def test_set_get_types(self, memory_cache, obj):
        memory_cache.serializer = NullSerializer()
        assert await memory_cache.set(Keys.KEY, obj) is True
        assert await memory_cache.get(Keys.KEY) is obj

    @pytest.mark.parametrize("obj", TYPES)
    async def test_add_get_types(self, memory_cache, obj):
        memory_cache.serializer = NullSerializer()
        assert await memory_cache.add(Keys.KEY, obj) is True
        assert await memory_cache.get(Keys.KEY) is obj

    @pytest.mark.parametrize("obj", TYPES)
    async def test_multi_set_multi_get_types(self, memory_cache, obj):
        memory_cache.serializer = NullSerializer()
        assert await memory_cache.multi_set([(Keys.KEY, obj)]) is True
        assert (await memory_cache.multi_get([Keys.KEY]))[0] is obj


class TestStringSerializer:
    TYPES = (1, 2.0, "hi", True, ["1", 1], {"key": "value"}, MyType())

    @pytest.mark.parametrize("obj", TYPES)
    async def test_set_get_types(self, cache, obj):
        cache.serializer = StringSerializer()
        assert await cache.set(Keys.KEY, obj) is True
        assert await cache.get(Keys.KEY) == str(obj)

    @pytest.mark.parametrize("obj", TYPES)
    async def test_add_get_types(self, cache, obj):
        cache.serializer = StringSerializer()
        assert await cache.add(Keys.KEY, obj) is True
        assert await cache.get(Keys.KEY) == str(obj)

    @pytest.mark.parametrize("obj", TYPES)
    async def test_multi_set_multi_get_types(self, cache, obj):
        cache.serializer = StringSerializer()
        assert await cache.multi_set([(Keys.KEY, obj)]) is True
        assert await cache.multi_get([Keys.KEY]) == [str(obj)]


class TestJsonSerializer:
    TYPES = (1, 2.0, "hi", True, ["1", 1], {"key": "value"})

    @pytest.mark.parametrize("obj", TYPES)
    async def test_set_get_types(self, cache, obj):
        cache.serializer = JsonSerializer()
        assert await cache.set(Keys.KEY, obj) is True
        assert await cache.get(Keys.KEY) == json.loads(json.dumps(obj))

    @pytest.mark.parametrize("obj", TYPES)
    async def test_add_get_types(self, cache, obj):
        cache.serializer = JsonSerializer()
        assert await cache.add(Keys.KEY, obj) is True
        assert await cache.get(Keys.KEY) == json.loads(json.dumps(obj))

    @pytest.mark.parametrize("obj", TYPES)
    async def test_multi_set_multi_get_types(self, cache, obj):
        cache.serializer = JsonSerializer()
        assert await cache.multi_set([(Keys.KEY, obj)]) is True
        assert await cache.multi_get([Keys.KEY]) == [json.loads(json.dumps(obj))]


class TestPickleSerializer:
    TYPES = (1, 2.0, "hi", True, ["1", 1], {"key": "value"}, MyType())

    @pytest.mark.parametrize("obj", TYPES)
    async def test_set_get_types(self, cache, obj):
        cache.serializer = PickleSerializer()
        assert await cache.set(Keys.KEY, obj) is True
        assert await cache.get(Keys.KEY) == pickle.loads(pickle.dumps(obj))

    @pytest.mark.parametrize("obj", TYPES)
    async def test_add_get_types(self, cache, obj):
        cache.serializer = PickleSerializer()
        assert await cache.add(Keys.KEY, obj) is True
        assert await cache.get(Keys.KEY) == pickle.loads(pickle.dumps(obj))

    @pytest.mark.parametrize("obj", TYPES)
    async def test_multi_set_multi_get_types(self, cache, obj):
        cache.serializer = PickleSerializer()
        assert await cache.multi_set([(Keys.KEY, obj)]) is True
        assert await cache.multi_get([Keys.KEY]) == [pickle.loads(pickle.dumps(obj))]


class TestAltSerializers:
    async def test_get_set_alt_serializer_functions(self, cache):
        cache.serializer = StringSerializer()
        await cache.set(Keys.KEY, "value", dumps_fn=lambda _: "v4lu3")
        assert await cache.get(Keys.KEY) == "v4lu3"
        assert await cache.get(Keys.KEY, loads_fn=lambda _: "value") == "value"

    async def test_get_set_alt_serializer_class(self, cache):
        my_serializer = MyTypeSchema()
        my_obj = MyType()
        cache.serializer = my_serializer
        await cache.set(Keys.KEY, my_obj)
        assert await cache.get(Keys.KEY) == my_serializer.loads(my_serializer.dumps(my_obj))
