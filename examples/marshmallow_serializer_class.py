import random
import string
import asyncio

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


class MarshmallowSerializer(Schema, BaseSerializer):  # type: ignore[misc]
    int_type = fields.Integer()
    str_type = fields.String()
    dict_type = fields.Dict()
    list_type = fields.List(fields.Integer())

    # marshmallow Schema class doesn't play nicely with multiple inheritance and won't call
    # BaseSerializer.__init__
    encoding = 'utf-8'

    @post_load
    def build_my_type(self, data, **kwargs):
        return RandomModel(**data)

    class Meta:
        strict = True


cache = Cache(serializer=MarshmallowSerializer(), namespace="main")


async def serializer():
    model = RandomModel()
    await cache.set("key", model)

    result = await cache.get("key")

    assert result.int_type == model.int_type
    assert result.str_type == model.str_type
    assert result.dict_type == model.dict_type
    assert result.list_type == model.list_type


def test_serializer():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(serializer())
    loop.run_until_complete(cache.delete("key"))


if __name__ == "__main__":
    test_serializer()
