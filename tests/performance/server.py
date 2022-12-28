import asyncio
import logging
import uuid

from aiohttp import web

from aiocache import Cache

logging.getLogger("aiohttp.access").propagate = False


class CacheManager:
    def __init__(self, backend: str):
        backends = {
            "memory": Cache.MEMORY,
            "redis": Cache.REDIS,
            "memcached": Cache.MEMCACHED,
        }
        self.cache = Cache(backends[backend])

    async def get(self, key):
        return await self.cache.get(key, timeout=0.1)

    async def set(self, key, value):
        return await self.cache.set(key, value, timeout=0.1)

    async def close(self, *_):
        await self.cache.close()


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


def run_server(backend: str) -> None:
    app = web.Application()
    app["cache"] = CacheManager(backend)
    app.on_shutdown.append(app["cache"].close)
    app.router.add_route("GET", "/", handler_get)
    web.run_app(app)
