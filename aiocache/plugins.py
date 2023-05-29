"""
This module implements different plugins you can attach to your cache instance. They
are coded in a collaborative so you can use multiple inheritance.
"""

from aiocache.base import API
from aiocache.backends.memory import SimpleMemoryCache

class BasePlugin:
    @classmethod
    def add_hook(cls, func, hooks):
        for hook in hooks:
            setattr(cls, hook, func)

    async def do_nothing(self, *args, **kwargs):
        pass


BasePlugin.add_hook(
    BasePlugin.do_nothing, ["pre_{}".format(method.__name__) for method in API.CMDS]
)
BasePlugin.add_hook(
    BasePlugin.do_nothing, ["post_{}".format(method.__name__) for method in API.CMDS]
)


class TimingPlugin(BasePlugin):
    """
    Calculates average, min and max times each command takes. The data is saved
    in the cache class as a dict attribute called ``profiling``. For example, to
    access the average time of the operation get, you can do ``cache.profiling['get_avg']``
    """

    @classmethod
    def save_time(cls, method):
        async def do_save_time(self, client, *args, took=0, **kwargs):
            if not hasattr(client, "profiling"):
                client.profiling = {}

            previous_total = client.profiling.get("{}_total".format(method), 0)
            previous_avg = client.profiling.get("{}_avg".format(method), 0)
            previous_max = client.profiling.get("{}_max".format(method), 0)
            previous_min = client.profiling.get("{}_min".format(method))

            client.profiling["{}_total".format(method)] = previous_total + 1
            client.profiling["{}_avg".format(method)] = previous_avg + (took - previous_avg) / (
                previous_total + 1
            )
            client.profiling["{}_max".format(method)] = max(took, previous_max)
            client.profiling["{}_min".format(method)] = (
                min(took, previous_min) if previous_min else took
            )

        return do_save_time


for method in API.CMDS:
    TimingPlugin.add_hook(
        TimingPlugin.save_time(method.__name__), ["post_{}".format(method.__name__)]
    )


class HitMissRatioPlugin(BasePlugin):
    """
    Calculates the ratio of hits the cache has. The data is saved in the cache class as a dict
    attribute called ``hit_miss_ratio``. For example, to access the hit ratio of the cache,
    you can do ``cache.hit_miss_ratio['hit_ratio']``. It also provides the "total" and "hits"
    keys.
    """

    async def post_get(self, client, key, took=0, ret=None, **kwargs):
        if not hasattr(client, "hit_miss_ratio"):
            client.hit_miss_ratio = {}
            client.hit_miss_ratio["total"] = 0
            client.hit_miss_ratio["hits"] = 0

        client.hit_miss_ratio["total"] += 1
        if ret is not None:
            client.hit_miss_ratio["hits"] += 1

        client.hit_miss_ratio["hit_ratio"] = (
            client.hit_miss_ratio["hits"] / client.hit_miss_ratio["total"]
        )

    async def post_multi_get(self, client, keys, took=0, ret=None, **kwargs):
        if not hasattr(client, "hit_miss_ratio"):
            client.hit_miss_ratio = {}
            client.hit_miss_ratio["total"] = 0
            client.hit_miss_ratio["hits"] = 0

        client.hit_miss_ratio["total"] += len(keys)
        for result in ret:
            if result is not None:
                client.hit_miss_ratio["hits"] += 1

        client.hit_miss_ratio["hit_ratio"] = (
            client.hit_miss_ratio["hits"] / client.hit_miss_ratio["total"]
        )


class LimitLengthPlugin(BasePlugin):
    """
    Limits the number of entries that the cache may contain.

    Example usage:
      c = Cache(cache_class=Cache.MEMORY, ttl=300, plugins=[LimitLength(max_length=2000)])

    Caveats:
    * Only works with the SimpleMemoryCache backend.
    * Entries are trimmed AFTER the new entry is added, so the cache may temporarily contain more entries than the specified limit.
    """

    def __init__(self, max_length: int = 1000):
        assert int(max_length) == max_length
        assert max_length >= 0
        self.max_length = int(max_length)

    def _check_support(self, client: SimpleMemoryCache):
        """
        Checks if the client is of the correct type.
        TODO: Ideally, this should be checked only once when the cache is created.
        """
        if not isinstance(client, SimpleMemoryCache):
            raise NotImplementedError(
                "LimitLength plugin only works with the SimpleMemoryCache backend."
            )

    async def post_set(self, client: SimpleMemoryCache, *args, **kwargs):
        """
        Drop extra records that exceed configured capacity.
        """
        self._check_support(client)
        current_length = len(client._cache)
        if current_length > self.max_length:
            # Sort by time of expiry. Delete the entries nearest to expiration first.
            a = list((client._handlers[k].when(), k)
                     for k in client._handlers.keys())
            a.sort()
            for _, k in a[:current_length - self.max_length]:
                await client.delete(k)

    async def post_multi_set(self, client: SimpleMemoryCache, *args, **kwargs):
        # post_set is enough. No special handling is needed for multi_set
        await self.post_set(client, *args, **kwargs)
