import tornado.web
import tornado.ioloop
from datetime import datetime
from aiocache import cached, SimpleMemoryCache
from aiocache.serializers import JsonSerializer


class MainHandler(tornado.web.RequestHandler):

    # Due some incompatibilities between tornado and asyncio, caches can't use the "ttl" feature
    # in order to make it work, you will have to specify it always to 0
    @cached(SimpleMemoryCache(serializer=JsonSerializer, timeout=0), key_builder= lambda x : "my_custom_key")
    async def time(self):
        return {"time": datetime.now().isoformat()}

    async def get(self):
        self.write(await self.time())


if __name__ == "__main__":
    tornado.ioloop.IOLoop.configure('tornado.platform.asyncio.AsyncIOLoop')
    app = tornado.web.Application([(r"/", MainHandler)])
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
