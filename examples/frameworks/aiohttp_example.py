from datetime import datetime
from aiohttp import web
from aiocache import cached
from aiocache.serializers import JsonSerializer


@cached(key="my_custom_key", serializer=JsonSerializer())
async def time():
    return {"time": datetime.now().isoformat()}


async def handle(request):
    return web.json_response(await time())


if __name__ == "__main__":
    app = web.Application()
    app.router.add_get('/', handle)

    web.run_app(app)
