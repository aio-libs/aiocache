import asyncio

import redis.asyncio as redis

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
        'host': "127.0.0.1",
        'port': 6379,
        'socket_connect_timeout': 1,
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
    # This generates a new instance every time! You can also use
    # `caches.create("alt", namespace="test", etc...)` to override extra args
    cache = caches.create("redis_alt")
    await cache.set("key", "value")

    assert await cache.get("key") == "value"
    assert isinstance(cache, Cache.REDIS)
    assert isinstance(cache.serializer, PickleSerializer)
    assert len(cache.plugins) == 2
    assert cache.client.connection_pool.connection_kwargs['host'] == "127.0.0.1"
    assert cache.client.connection_pool.connection_kwargs['socket_connect_timeout'] == 1
    assert cache.client.connection_pool.connection_kwargs['port'] == 6379
    await cache.close()


async def test_alias():
    await default_cache()
    await alt_cache()

    cache = Cache(Cache.REDIS, client=redis.Redis())
    await cache.delete("key")
    await cache.close()

    await caches.get("default").close()


if __name__ == "__main__":
    asyncio.run(test_alias())
