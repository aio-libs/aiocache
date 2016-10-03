import asyncio
import aiocache

from collections import namedtuple

from aiocache import cached

Result = namedtuple('Result', "content, status")

aiocache.config_default_cache()

async def global_cache():
    await aiocache.default_cache.set("key", "value")
    await asyncio.sleep(1)
    return await aiocache.default_cache.get("key")


@cached(ttl=10)
async def decorator_example():
    print("First ASYNC non cached call...")
    await asyncio.sleep(1)
    return Result("content", 200)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(global_cache()))
    print(loop.run_until_complete(decorator_example()))
    print(loop.run_until_complete(decorator_example()))
    print(loop.run_until_complete(decorator_example()))
