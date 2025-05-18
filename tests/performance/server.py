import asyncio
import logging
import uuid
import sys
from typing import AsyncIterator

from aiohttp import web

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing import Any as Self

logging.getLogger("aiohttp.access").propagate = False


class CacheManager:
    def __init__(self, backend: str):
        if backend == "valkey":
            from aiocache.backends.valkey import ValkeyCache
            from glide import GlideClientConfiguration, NodeAddress

            cache = ValkeyCache(GlideClientConfiguration(addresses=[NodeAddress()], database_id=0))
        elif backend == "memcached":
            from aiocache.backends.memcached import MemcachedCache
            cache = MemcachedCache()
        elif backend == "memory":
            from aiocache.backends.memory import SimpleMemoryCache
            cache = SimpleMemoryCache()
        else:
            raise ValueError("Invalid backend")
        self.cache = cache

    async def get(self, key):
        return await self.cache.get(key, timeout=0.1)

    async def set(self, key, value):
        return await self.cache.set(key, value, timeout=0.1)

    async def __aenter__(self) -> Self:
        await self.cache.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        await self.cache.__aexit__(exc_type, exc, tb)


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


def cache_manager_ctx(backend: str) -> Callable[[web.Application], AsyncIterator[None]]:
    async def ctx(app: web.Application) -> AsyncIterator[None]:
        async with CacheManager(backend) as cm
            app[cache_key] = cm
            yield

    return ctx


def run_server(backend: str) -> None:
    app = web.Application()
    app.cleanup_ctx.append(cache_manager_ctx(backend))
    app.router.add_route("GET", "/", handler_get)
    web.run_app(app)
