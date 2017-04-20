import asyncio

from aiocache import settings, caches, SimpleMemoryCache, RedisCache
from aiocache.serializers import DefaultSerializer, PickleSerializer

settings.set_config({
    'default': {
        'cache': "aiocache.SimpleMemoryCache",
        'serializer': {
            'class': "aiocache.serializers.DefaultSerializer"
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
    cache = caches['default']   # This always returns the same instance
    await cache.set("key", "value")

    assert await cache.get("key") == "value"
    assert isinstance(cache, SimpleMemoryCache)
    assert isinstance(cache.serializer, DefaultSerializer)


async def alt_cache():
    cache = caches['redis_alt']   # This always returns the same instance
    await cache.set("key", "value")

    assert await cache.get("key") == "value"
    assert isinstance(cache, RedisCache)
    assert isinstance(cache.serializer, PickleSerializer)
    assert len(cache.plugins) == 2
    assert cache.endpoint == "127.0.0.1"
    assert cache.timeout == 1
    assert cache.port == 6379


def test_alias():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(default_cache())
    loop.run_until_complete(alt_cache())

    loop.run_until_complete(RedisCache().delete("key"))


if __name__ == "__main__":
    test_alias()
