import asyncio
import random
import logging

from aiocache import Cache
from aiocache.plugins import HitMissRatioPlugin, TimingPlugin, BasePlugin, LimitLengthPlugin


logger = logging.getLogger(__name__)


class MyCustomPlugin(BasePlugin):

    async def pre_set(self, *args, **kwargs):
        logger.info("I'm the pre_set hook being called with %s %s" % (args, kwargs))

    async def post_set(self, *args, **kwargs):
        logger.info("I'm the post_set hook being called with %s %s" % (args, kwargs))


cache = Cache(
    plugins=[HitMissRatioPlugin(), TimingPlugin(), LimitLengthPlugin(max_length = 4), MyCustomPlugin()],
    namespace="main")


async def run():
    await cache.set("a", "1")
    await cache.set("b", "2")
    await cache.set("c", "3")
    await cache.set("d", "4")
    await cache.set("e", "5")
    await cache.set("f", "6")
    #entries "a" and "b" above will get dropped because max_length is 4

    possible_keys = ["a", "b", "c", "d", "e", "f"]

    for t in range(1000):
        await cache.get(random.choice(possible_keys))

    assert cache.hit_miss_ratio["hit_ratio"] > 0.5
    assert cache.hit_miss_ratio["total"] == 1000

    assert cache.profiling["get_min"] > 0
    assert cache.profiling["set_min"] > 0
    assert cache.profiling["get_max"] > 0
    assert cache.profiling["set_max"] > 0

    print(cache.hit_miss_ratio)
    print(cache.profiling)


async def test_run():
    await run()
    await cache.delete("a")
    await cache.delete("b")
    await cache.delete("c")
    await cache.delete("d")


if __name__ == "__main__":
    asyncio.run(test_run())
