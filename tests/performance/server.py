import argparse
import asyncio
import logging
import uuid

from aiohttp import web

from aiocache import Cache


logging.getLogger("aiohttp.access").propagate = False


AIOCACHE_BACKENDS = {
    "memory": Cache(Cache.MEMORY),
    "redis": Cache(Cache.REDIS),
    "memcached": Cache(Cache.MEMCACHED),
}


class CacheManager:
    def __init__(self, backend):
        self.cache = AIOCACHE_BACKENDS.get(backend)

    async def get(self, key):
        return await self.cache.get(key, timeout=0.1)

    async def set(self, key, value):
        return await self.cache.set(key, value, timeout=0.1)


async def handler_get(req):
    try:
        data = await req.app["cache"].get("testkey")
        if data:
            return web.Response(text=data)
    except asyncio.TimeoutError:
        return web.Response(status=404)

    data = str(uuid.uuid4())
    await req.app["cache"].set("testkey", data)
    return web.Response(text=str(data))


def run_server(backend, loop=None):
    if loop:
        asyncio.set_event_loop(loop)
    app = web.Application()
    app["cache"] = CacheManager(backend)
    app.router.add_route("GET", "/", handler_get)
    web.run_app(app)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b", dest="backend", required=True, choices=["memory", "redis", "memcached"]
    )
    args = parser.parse_args()
    run_server(args.backend)
