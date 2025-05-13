import asyncio
import json

from glide import GlideClientConfiguration, NodeAddress

from marshmallow import Schema, fields, post_load

from aiocache import ValkeyCache


addresses = [NodeAddress("localhost", 6379)]
config = GlideClientConfiguration(addresses=addresses, database_id=0)


class MyType:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class MyTypeSchema(Schema):
    x = fields.Number()
    y = fields.Number()

    @post_load
    def build_object(self, data, **kwargs):
        return MyType(data["x"], data["y"])


def dumps(value):
    return MyTypeSchema().dumps(value)


def loads(value):
    return MyTypeSchema().loads(value)


async def serializer_function():
    async with ValkeyCache(config=config, namespace="main") as cache:
        await cache.set("key", MyType(1, 2), dumps_fn=dumps)

        obj = await cache.get("key", loads_fn=loads)

        assert obj.x == 1
        assert obj.y == 2
        assert await cache.get("key") == json.loads(('{"y": 2.0, "x": 1.0}'))
        assert json.loads(await cache.raw("get", "main:key")) == {"y": 2.0, "x": 1.0}


async def test_serializer_function():
    await serializer_function()
    async with ValkeyCache(config=config, namespace="main") as cache:
        await cache.delete("key")


if __name__ == "__main__":
    asyncio.run(test_serializer_function())
