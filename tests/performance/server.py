import asyncio
import logging
import uuid

import redis.asyncio as redis
from aiohttp import web

logging.getLogger("aiohttp.access").propagate = False


class CacheManager:
    def __init__(self, backend: str):
        if backend == "redis":
            from aiocache.backends.redis import RedisCache
            cache = RedisCache(
                client=redis.Redis(
                    host="127.0.0.1",
                    port=6379,
                    db=0,
                    password=None,
                    decode_responses=False,
                )
            )
        elif backend == "memcached":
            from aiocache.backends.memcached import MemcachedCache
            cache = MemcachedCache()
        elif backend == "memory":
            from aiocache.backends.memory import MemoryCache
            cache = MemoryCache()
        else:
            raise ValueError("Invalid backend")
        self.cache = cache

    async def get(self, key):
        return await self.cache.get(key, timeout=0.1)

    async def set(self, key, value):
        return await self.cache.set(key, value, timeout=0.1)

    async def close(self, *_):
        await self.cache.close()


cache_key = web.AppKey("cache_key", CacheManager)


async def handler_get(req: web.Request) -> web.Response:
    try:
        data = await req.app[cache_key].get("testkey")
        if data:
            return web.Response(text=data)
    except asyncio.TimeoutError:
        return web.Response(status=404)

    data = str(uuid.uuid4())
    await req.app[cache_key].set("testkey", data)
    return web.Response(text=str(data))


def run_server(backend: str) -> None:
    app = web.Application()
    app[cache_key] = CacheManager(backend)
    app.on_shutdown.append(app[cache_key].close)
    app.router.add_route("GET", "/", handler_get)
    web.run_app(app)
