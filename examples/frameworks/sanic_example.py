"""
Example of caching using aiocache package:

    /: Does a 3 seconds sleep. Only the first time because its using the `cached` decorator
    /reuse: Returns the data stored in "main" endpoint
"""

import asyncio

from sanic import Sanic
from sanic.response import json
from sanic.log import logger
from aiocache import cached, Cache
from aiocache.serializers import JsonSerializer

app = Sanic(__name__)


@cached(key="my_custom_key", serializer=JsonSerializer())
async def expensive_call():
    logger.info("Expensive has been called")
    await asyncio.sleep(3)
    return {"test": True}


async def reuse_data():
    cache = Cache(serializer=JsonSerializer())  # Not ideal to define here
    data = await cache.get("my_custom_key")  # Note the key is defined in `cached` decorator
    return data


@app.route("/")
async def main(request):
    logger.info("Received GET /")
    return json(await expensive_call())


@app.route("/reuse")
async def reuse(request):
    logger.info("Received GET /reuse")
    return json(await reuse_data())


app.run(host="0.0.0.0", port=8000)
