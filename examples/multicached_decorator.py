import asyncio

from aiocache import multi_cached, Cache

DICT = {
    'a': "Z",
    'b': "Y",
    'c': "X",
    'd': "W"
}


@multi_cached("ids", cache=Cache.REDIS, namespace="main")
async def multi_cached_ids(ids=None):
    return {id_: DICT[id_] for id_ in ids}


@multi_cached("keys", cache=Cache.REDIS, namespace="main")
async def multi_cached_keys(keys=None):
    return {id_: DICT[id_] for id_ in keys}


cache = Cache(Cache.REDIS, endpoint="127.0.0.1", port=6379, namespace="main")


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
