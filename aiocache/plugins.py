"""
This module implements different plugins you can attach to your cache instance. They
are coded in a collaborative so you can use multiple inheritance.
"""
import time


def plugin_pipeline(func):
    async def wrapper(self, *args, **kwargs):
        start = time.time()
        for plugin in self.plugins:
            await getattr(plugin, "pre_{}".format(func.__name__))(self, *args, **kwargs)

        ret = await func(self, *args, **kwargs)

        for plugin in self.plugins:
            await getattr(
                plugin, "post_{}".format(func.__name__))(
                    self, *args, took=time.time() - start, ret=ret, **kwargs)
        return ret
    return wrapper


class BasePlugin:
    _HOOKED_METHODS = [
        'add',
        'get',
        'multi_get',
        'set',
        'multi_set',
        'delete',
        'exists',
        'clear',
        'raw',
    ]


async def placeholder(self, client, *args, **kwargs):
    pass

for method in BasePlugin._HOOKED_METHODS:
    setattr(BasePlugin, "pre_{}".format(method), classmethod(placeholder))
    setattr(BasePlugin, "post_{}".format(method), classmethod(placeholder))


class HitMissRatioPlugin(BasePlugin):
    async def post_get(self, client, key, took=0, ret=None):
        if hasattr(client, "hit_miss_ratio"):
            client.hit_miss_ratio["total"] += 1
            if ret is not None:
                client.hit_miss_ratio["hits"] += 1
            else:
                client.hit_miss_ratio["miss"] += 1
        else:
            client.hit_miss_ratio = {}
            client.hit_miss_ratio["total"] = 1
            if ret is not None:
                client.hit_miss_ratio["hits"] = 1
                client.hit_miss_ratio["miss"] = 0
            else:
                client.hit_miss_ratio["hits"] = 0
                client.hit_miss_ratio["miss"] = 1

        client.hit_miss_ratio['hit_ratio'] = \
            client.hit_miss_ratio["hits"] / client.hit_miss_ratio["total"]
        client.hit_miss_ratio['miss_ratio'] = \
            client.hit_miss_ratio["miss"] / client.hit_miss_ratio["total"]
