import asyncio

from collections import namedtuple

from aiocache import cached
from aiocache.serializers import PickleSerializer

Result = namedtuple('Result', "content, status")


@cached(ttl=10, serializer=PickleSerializer)
async def async_main():
    print("First ASYNC non cached call...")
    await asyncio.sleep(1)
    return Result("content", 200)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(async_main()))
    print(loop.run_until_complete(async_main()))
    print(loop.run_until_complete(async_main()))
    print(loop.run_until_complete(async_main()))
