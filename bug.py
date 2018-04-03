import asyncio
import logging
from aiocache import cached_stampede
from aiohttp import web

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)


@cached_stampede(lease=1)
async def test_func(val):
    logging.info('calling function...')
    await asyncio.sleep(5)
    return 1

async def test(request):
    val = request.match_info['val']
    await test_func(val)
    return web.Response(text=f"Val is {val}")

app = web.Application()
app.router.add_get('/h/{val}', test)
web.run_app(app)
