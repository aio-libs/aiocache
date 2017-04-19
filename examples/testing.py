import asyncio

from asynctest import Mock

from aiocache.base import BaseCache


async def async_main():
    mocked_cache = Mock(spec=BaseCache)
    mocked_cache.get.return_value = "World"
    print(await mocked_cache.get("hello"))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(async_main()))
