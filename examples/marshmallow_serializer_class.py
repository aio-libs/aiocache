import random
import string
import asyncio
from typing import Any

from marshmallow import fields, Schema, post_load

from aiocache import Cache
from aiocache.serializers import BaseSerializer


class RandomModel:
    MY_CONSTANT = "CONSTANT"

    def __init__(self, int_type=None, str_type=None, dict_type=None, list_type=None):
        self.int_type = int_type or random.randint(1, 10)
        self.str_type = str_type or random.choice(string.ascii_lowercase)
        self.dict_type = dict_type or {}
        self.list_type = list_type or []

    def __eq__(self, obj):
        return self.__dict__ == obj.__dict__


class RandomSchema(Schema):
    int_type = fields.Integer()
    str_type = fields.String()
    dict_type = fields.Dict()
    list_type = fields.List(fields.Integer())

    @post_load
    def build_my_type(self, data, **kwargs):
        return RandomModel(**data)

    class Meta:
        strict = True


class MarshmallowSerializer(BaseSerializer):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.schema = RandomSchema()

    def dumps(self, value: Any) -> str:
        return self.schema.dumps(value)

    def loads(self, value: str) -> Any:
        return self.schema.loads(value)


cache = Cache(serializer=MarshmallowSerializer(), namespace="main")


async def serializer():
    model = RandomModel()
    await cache.set("key", model)

    result = await cache.get("key")

    assert result.int_type == model.int_type
    assert result.str_type == model.str_type
    assert result.dict_type == model.dict_type
    assert result.list_type == model.list_type


async def test_serializer():
    await serializer()
    await cache.delete("key")


if __name__ == "__main__":
    asyncio.run(test_serializer())
