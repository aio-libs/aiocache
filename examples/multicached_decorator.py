import asyncio

import redis.asyncio as redis

from aiocache import multi_cached
from aiocache import RedisCache

DICT = {
    'a': "Z",
    'b': "Y",
    'c': "X",
    'd': "W"
}

cache = RedisCache(namespace="main", client=redis.Redis())


@multi_cached("ids", cache=cache)
async def multi_cached_ids(ids=None):
    return {id_: DICT[id_] for id_ in ids}


@multi_cached("keys", cache=cache)
async def multi_cached_keys(keys=None):
    return {id_: DICT[id_] for id_ in keys}


async def test_multi_cached():
    await multi_cached_ids(ids=("a", "b"))
    await multi_cached_ids(ids=("a", "c"))
    await multi_cached_keys(keys=("d",))

    assert await cache.exists("a")
    assert await cache.exists("b")
    assert await cache.exists("c")
    assert await cache.exists("d")

    await cache.delete("a")
    await cache.delete("b")
    await cache.delete("c")
    await cache.delete("d")
    await cache.close()


if __name__ == "__main__":
    asyncio.run(test_multi_cached())
