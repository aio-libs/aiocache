import asyncio
import json

import redis.asyncio as redis

from marshmallow import Schema, fields, post_load

from aiocache import RedisCache


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


cache = RedisCache(namespace="main", client=redis.Redis())


async def serializer_function():
    await cache.set("key", MyType(1, 2), dumps_fn=dumps)

    obj = await cache.get("key", loads_fn=loads)

    assert obj.x == 1
    assert obj.y == 2
    assert await cache.get("key") == json.loads(('{"y": 2.0, "x": 1.0}'))
    assert json.loads(await cache.raw("get", "main:key")) == {"y": 2.0, "x": 1.0}


async def test_serializer_function():
    await serializer_function()
    await cache.delete("key")
    await cache.close()


if __name__ == "__main__":
    asyncio.run(test_serializer_function())
