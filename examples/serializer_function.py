import asyncio
import json

from marshmallow import Schema, fields, post_load
from aiocache import Cache


class MyType:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class MyTypeSchema(Schema):
    x = fields.Number()
    y = fields.Number()

    @post_load
    def build_object(self, data, **kwargs):
        return MyType(data['x'], data['y'])


def dumps(value):
    return MyTypeSchema().dumps(value)


def loads(value):
    return MyTypeSchema().loads(value)


cache = Cache(Cache.REDIS, namespace="main")


async def serializer_function():
    await cache.set("key", MyType(1, 2), dumps_fn=dumps)

    obj = await cache.get("key", loads_fn=loads)

    assert obj.x == 1
    assert obj.y == 2
    assert await cache.get("key") == json.loads(('{"y": 2.0, "x": 1.0}'))
    assert json.loads(await cache.raw("get", "main:key")) == {"y": 2.0, "x": 1.0}


def test_serializer_function():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(serializer_function())
    loop.run_until_complete(cache.delete("key"))
    loop.run_until_complete(cache.close())


if __name__ == "__main__":
    test_serializer_function()
