import asyncio

from asynctest import CoroutineMock

from aiocache.backends.base import BaseCache


async def async_main():
    mocked_cache = CoroutineMock(spec=BaseCache)
    mocked_cache.get.return_value = "World"
    print(await mocked_cache.get("hello"))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(async_main()))
