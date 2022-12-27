import argparse
import asyncio
import logging
import uuid

from aiohttp import web

from aiocache import Cache


logging.getLogger("aiohttp.access").propagate = False


AIOCACHE_BACKENDS = {
    "memory": (Cache(Cache.MEMORY), 0.1),
    "redis": (Cache(Cache.REDIS), 0.1),
    "memcached": (Cache(Cache.MEMCACHED), 10),
}


class CacheManager:
    def __init__(self, backend: str):
        self.cache, self.timeout = AIOCACHE_BACKENDS[backend]

    async def get(self, key):
        return await self.cache.get(key, timeout=self.timeout)

    async def set(self, key, value):
        return await self.cache.set(key, value, timeout=self.timeout)


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


def run_server(backend):
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
