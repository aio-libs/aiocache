"""
This module implements different plugins you can attach to your cache instance. They
are coded in a collaborative so you can use multiple inheritance.
"""
import os
import time


def plugin_pipeline(func):
    async def wrapper(self, *args, **kwargs):
        if not os.getenv('AIOCACHE_DISABLE') == "1":
            start = time.time()
            for plugin in self.plugins:
                await getattr(plugin, "pre_{}".format(func.__name__))(self, *args, **kwargs)

            ret = await func(self, *args, **kwargs)

            for plugin in self.plugins:
                await getattr(
                    plugin, "post_{}".format(func.__name__))(
                        self, *args, took=time.time() - start, ret=ret, **kwargs)
            return ret
        else:
            return BasePlugin.NULL_RETURN.get(func.__name__)
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

    NULL_RETURN = {
        'get': None,
        'set': True,
        'multi_get': [],
        'multi_set': True,
        'add': True,
        'delete': 0,
        'exists': False,
        'clear': True,
        'raw': None,
    }


async def do_nothing(self, client, *args, **kwargs):
    pass

for method in BasePlugin._HOOKED_METHODS:
    setattr(BasePlugin, "pre_{}".format(method), classmethod(do_nothing))
    setattr(BasePlugin, "post_{}".format(method), classmethod(do_nothing))


class TimingPlugin(BasePlugin):
    """
    Calculates average, min and max times each command took. The data is saved
    in the cache class as a dict attribute called ``profiling``. For example, to
    access the average time of the operation get, you can do ``cache.profiling['get_avg']``
    """


def save_time(method):

    async def do_save_time(self, client, *args, took=0, **kwargs):
        if not hasattr(client, "profiling"):
            client.profiling = {}

        previous_total = client.profiling.get("{}_total".format(method), 0)
        previous_avg = client.profiling.get("{}_avg".format(method), 0)
        previous_max = client.profiling.get("{}_max".format(method), 0)
        previous_min = client.profiling.get("{}_min".format(method))

        client.profiling["{}_total".format(method)] = previous_total + 1
        client.profiling["{}_avg".format(method)] = \
            previous_avg + (took - previous_avg) / (previous_total + 1)
        client.profiling["{}_max".format(method)] = max(took, previous_max)
        client.profiling["{}_min".format(method)] = \
            min(took, previous_min) if previous_min else took

    return do_save_time


for method in TimingPlugin._HOOKED_METHODS:
    setattr(TimingPlugin, "post_{}".format(method), classmethod(save_time(method)))


class HitMissRatioPlugin(BasePlugin):
    """
    Calculates the ratio of hits the cache has. The data is saved in the cache class as a dict
    attribute called ``hit_miss_ratio``. For example, to access the hit ratio of the cache,
    you can do ``cache.hit_miss_ratio['hit_ratio']``. It also provides the "total" and "hits"
    keys.
    """
    async def post_get(self, client, key, took=0, ret=None):
        if not hasattr(client, "hit_miss_ratio"):
            client.hit_miss_ratio = {}
            client.hit_miss_ratio["total"] = 0
            client.hit_miss_ratio["hits"] = 0

        client.hit_miss_ratio["total"] += 1
        if ret is not None:
            client.hit_miss_ratio["hits"] += 1

        client.hit_miss_ratio['hit_ratio'] = \
            client.hit_miss_ratio["hits"] / client.hit_miss_ratio["total"]

    async def post_multi_get(self, client, keys, took=0, ret=None):
        if not hasattr(client, "hit_miss_ratio"):
            client.hit_miss_ratio = {}
            client.hit_miss_ratio["total"] = 0
            client.hit_miss_ratio["hits"] = 0

        client.hit_miss_ratio["total"] += len(keys)
        for result in ret:
            if result is not None:
                client.hit_miss_ratio["hits"] += 1

        client.hit_miss_ratio['hit_ratio'] = \
            client.hit_miss_ratio["hits"] / client.hit_miss_ratio["total"]
