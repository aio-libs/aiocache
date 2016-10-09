import asyncio

from marshmallow import Schema, fields
from aiocache import RedisCache


class MyType:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class MyTypeSchema(Schema):
    x = fields.Number()
    y = fields.Number()


def serialize(value):
    # Current implementation can't deal directly with dicts so we must cast to string
    return str(MyTypeSchema().dump(value).data)


def deserialize(value):
    return dict(MyTypeSchema().load(value).data)


async def main():
    cache = RedisCache(namespace="main")
    await cache.set("key", MyType(1, 2), dumps_fn=serialize)
    print(await cache.get("key", loads_fn=deserialize))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
