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


def test_multi_cached():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(multi_cached_ids(ids=['a', 'b']))
    loop.run_until_complete(multi_cached_ids(ids=['a', 'c']))
    loop.run_until_complete(multi_cached_keys(keys=['d']))

    assert loop.run_until_complete(cache.exists('a'))
    assert loop.run_until_complete(cache.exists('b'))
    assert loop.run_until_complete(cache.exists('c'))
    assert loop.run_until_complete(cache.exists('d'))

    loop.run_until_complete(cache.delete("a"))
    loop.run_until_complete(cache.delete("b"))
    loop.run_until_complete(cache.delete("c"))
    loop.run_until_complete(cache.delete("d"))
    loop.run_until_complete(cache.close())


if __name__ == "__main__":
    test_multi_cached()
