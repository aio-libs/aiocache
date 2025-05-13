import asyncio

from glide import GlideClientConfiguration, NodeAddress

from aiocache import multi_cached
from aiocache import ValkeyCache

DICT = {"a": "Z", "b": "Y", "c": "X", "d": "W"}

addresses = [NodeAddress("localhost", 6379)]
config = GlideClientConfiguration(addresses=addresses, database_id=0)
cache = ValkeyCache(config=config, namespace="main")


@multi_cached(cache, keys_from_attr="ids")
async def multi_cached_ids(ids=None):
    return {id_: DICT[id_] for id_ in ids}


@multi_cached(cache, keys_from_attr="keys")
async def multi_cached_keys(keys=None):
    return {id_: DICT[id_] for id_ in keys}


async def test_multi_cached():
    await multi_cached_ids(ids=("a", "b"))
    await multi_cached_ids(ids=("a", "c"))
    await multi_cached_keys(keys=("d",))

    async with cache:
        assert await cache.exists("a")
        assert await cache.exists("b")
        assert await cache.exists("c")
        assert await cache.exists("d")

        await cache.delete("a")
        await cache.delete("b")
        await cache.delete("c")
        await cache.delete("d")


if __name__ == "__main__":
    asyncio.run(test_multi_cached())
