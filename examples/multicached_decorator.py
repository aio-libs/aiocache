import asyncio

from aiocache import multi_cached, RedisCache

DICT = {
    'a': "Z",
    'b': "Y",
    'c': "X",
    'd': "W"
}


@multi_cached("ids", backend=RedisCache, namespace="main:")
async def async_main(ids=None):
    print("ASYNC non cached call...")
    return {id_: DICT[id_] for id_ in ids}


@multi_cached("keys", backend=RedisCache, namespace="main:")
async def async_second_main(keys=None):
    print("ASYNC non cached call...")
    return {id_: DICT[id_] for id_ in keys}


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(async_main(ids=['a', 'b'])))
    print(loop.run_until_complete(async_main(ids=['a', 'b'])))
    print(loop.run_until_complete(async_second_main(keys=['a', 'b'])))
    print(loop.run_until_complete(async_second_main(keys=['a', 'd'])))
