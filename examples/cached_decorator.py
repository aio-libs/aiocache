import asyncio

from collections import namedtuple

from aiocache import cached, Cache, caches
from aiocache.serializers import PickleSerializer
from aiocache.serializers import StringSerializer

Result = namedtuple('Result', "content, status")


@cached(
    ttl=10, cache=Cache.REDIS, key="key", serializer=PickleSerializer(),
    port=6379, namespace="main")
async def cached_call():
    return Result("content", 200)


async def test_cached():
    await test_cached_redis()
    await test_cached_alias_build_key()


async def test_cached_redis():
    async with Cache(Cache.REDIS, endpoint="127.0.0.1", port=6379, namespace="main") as cache:
        await cached_call()
        exists = await cache.exists("key")
        assert exists is True
        await cache.delete("key")


def build_key(key, namespace=None):
    # TODO(PY311): Remove str()
    ns = namespace if namespace is not None else ''
    sep = ':' if namespace else ''
    return f'{ns}{sep}{str(key)}'


caches.add(
    'custom',
    {
        'cache': Cache.MEMORY,
        'serializer': {
            'class': StringSerializer,
        },
        'namespace': "demo",
        'key_builder': build_key,
    },
)


async def test_cached_alias_build_key():
    """Decorate a function with an aliased cache that uses a namespace"""
    async with caches.get("custom") as cache:  # This always returns the same instance
        @cached(alias="custom")
        async def custom_cached_call():
            return "result"

        await custom_cached_call()
        decorator = cached(alias="custom")
        key = decorator.get_cache_key(custom_cached_call, (), {})
        exists = await cache.exists(key)
        assert exists is True
        exists = await cache.exists(key, namespace="demo")
        assert exists is True
        await cache.delete(key)
        exists = await cache.exists(key)
        assert exists is False


if __name__ == "__main__":
    asyncio.run(test_cached())
