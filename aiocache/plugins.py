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
                    self, *args, took=time.time() - start, **kwargs)
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
