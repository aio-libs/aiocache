import asyncio
import logging
from datetime import datetime
from aiohttp import web
from aiocache import cached
from aiocache.serializers import JsonSerializer


@cached(key="function_key", serializer=JsonSerializer())
async def time():
    return {"time": datetime.now().isoformat()}


async def handle(request):
    return web.json_response(await time())


# It is also possible to cache the whole route, but for this you will need to
# override `cached.get_from_cache` and regenerate the response since aiohttp
# forbids reusing responses
class CachedOverride(cached):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_from_cache(self, key):
        try:
            value = await self.cache.get(key)
            if type(value) == web.Response:
                return web.Response(
                    body=value.body,
                    status=value.status,
                    reason=value.reason,
                    headers=value.headers,
                )
            return value
        except Exception:
            logging.exception("Couldn't retrieve %s, unexpected error", key)


@CachedOverride(key="route_key", serializer=JsonSerializer())
async def handle2(request):
    return web.json_response(await asyncio.sleep(3))


if __name__ == "__main__":
    app = web.Application()
    app.router.add_get('/handle', handle)
    app.router.add_get('/handle2', handle2)

    web.run_app(app)
