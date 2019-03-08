import asyncio

from aiocache import caches, Cache
from aiocache.serializers import StringSerializer, PickleSerializer

caches.set_config({
    'default': {
        'cache': "aiocache.SimpleMemoryCache",
        'serializer': {
            'class': "aiocache.serializers.StringSerializer"
        }
    },
    'redis_alt': {
        'cache': "aiocache.RedisCache",
        'endpoint': "127.0.0.1",
        'port': 6379,
        'timeout': 1,
        'serializer': {
            'class': "aiocache.serializers.PickleSerializer"
        },
        'plugins': [
            {'class': "aiocache.plugins.HitMissRatioPlugin"},
            {'class': "aiocache.plugins.TimingPlugin"}
        ]
    }
})


async def default_cache():
    cache = caches.get('default')   # This always returns the same instance
    await cache.set("key", "value")

    assert await cache.get("key") == "value"
    assert isinstance(cache, Cache.MEMORY)
    assert isinstance(cache.serializer, StringSerializer)


async def alt_cache():
    # This generates a new instance every time! You can also use `caches.create('alt')`
    # or even `caches.create('alt', namespace="test", etc...)` to override extra args
    cache = caches.create(**caches.get_alias_config('redis_alt'))
    await cache.set("key", "value")

    assert await cache.get("key") == "value"
    assert isinstance(cache, Cache.REDIS)
    assert isinstance(cache.serializer, PickleSerializer)
    assert len(cache.plugins) == 2
    assert cache.endpoint == "127.0.0.1"
    assert cache.timeout == 1
    assert cache.port == 6379
    await cache.close()


def test_alias():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(default_cache())
    loop.run_until_complete(alt_cache())

    cache = Cache(Cache.REDIS)
    loop.run_until_complete(cache.delete("key"))
    loop.run_until_complete(cache.close())

    loop.run_until_complete(caches.get('default').close())


if __name__ == "__main__":
    test_alias()
