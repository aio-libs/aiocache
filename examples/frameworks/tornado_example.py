import tornado.web
import tornado.ioloop
from datetime import datetime
from aiocache import cached
from aiocache.serializers import JsonSerializer


class MainHandler(tornado.web.RequestHandler):

    @cached(key="my_custom_key", serializer=JsonSerializer(), timeout=0)
    async def time(self):
        return {"time": datetime.now().isoformat()}

    async def get(self):
        self.write(await self.time())


if __name__ == "__main__":
    tornado.ioloop.IOLoop.configure('tornado.platform.asyncio.AsyncIOLoop')
    app = tornado.web.Application([(r"/", MainHandler)])
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
