from sanic import Sanic
from sanic.response import json
from sanic.log import log
from datetime import datetime
from aiocache import cached
from aiocache.serializers import JsonSerializer

app = Sanic(__name__)


@cached(key="my_custom_key", serializer=JsonSerializer())
async def time():
    return {"time": datetime.now().isoformat()}


@app.route("/")
async def test(request):
    log.info("Received GET /")
    return json(await time())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
