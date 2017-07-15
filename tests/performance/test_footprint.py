import pytest
import time

import aioredis
import aiomcache


@pytest.fixture
def aioredis_pool(event_loop):
    return event_loop.run_until_complete(
        aioredis.create_pool(("127.0.0.1", 6379), maxsize=1))


class TestRedis:

    @pytest.mark.asyncio
    async def test_redis_getsetdel(self, aioredis_pool, redis_cache):
        N = 10000
        aioredis_total_time = 0
        for n in range(N):
            start = time.time()
            with await aioredis_pool as redis:
                await redis.set("hi", "value")
            with await aioredis_pool as redis:
                await redis.get("hi")
            with await aioredis_pool as redis:
                await redis.delete("hi")
            aioredis_total_time += time.time() - start

        aiocache_total_time = 0
        for n in range(N):
            start = time.time()
            await redis_cache.set("hi", "value", timeout=0)
            await redis_cache.get("hi", timeout=0)
            await redis_cache.delete("hi", timeout=0)
            aiocache_total_time += time.time() - start

        print("\n{:0.2f}/{:0.2f}: {:0.2f}".format(
            aiocache_total_time, aioredis_total_time, aiocache_total_time/aioredis_total_time))
        print("aiocache avg call: {:0.5f}s".format(
            aiocache_total_time/N))
        print("aioredis avg call: {:0.5f}s".format(
            aioredis_total_time/N))
        assert aiocache_total_time/aioredis_total_time < 1.30

    @pytest.mark.asyncio
    async def test_redis_multigetsetdel(self, aioredis_pool, redis_cache):
        N = 5000
        aioredis_total_time = 0
        values = ["a", "b", "c", "d", "e", "f"]
        for n in range(N):
            start = time.time()
            with await aioredis_pool as redis:
                await redis.mset(*[x for x in values*2])
            with await aioredis_pool as redis:
                await redis.mget(*values)
            for k in values:
                with await aioredis_pool as redis:
                    await redis.delete(k)
            aioredis_total_time += time.time() - start

        aiocache_total_time = 0
        for n in range(N):
            start = time.time()
            await redis_cache.multi_set([(x, x) for x in values], timeout=0)
            await redis_cache.multi_get(values, timeout=0)
            for k in values:
                await redis_cache.delete(k, timeout=0)
            aiocache_total_time += time.time() - start

        print("\n{:0.2f}/{:0.2f}: {:0.2f}".format(
            aiocache_total_time, aioredis_total_time, aiocache_total_time/aioredis_total_time))
        print("aiocache avg call: {:0.5f}s".format(
            aiocache_total_time/N))
        print("aioredis avg call: {:0.5f}s".format(
            aioredis_total_time/N))
        assert aiocache_total_time/aioredis_total_time < 1.35


@pytest.fixture
def aiomcache_pool():
    yield aiomcache.Client("127.0.0.1", 11211, pool_size=1)


class TestMemcached:

    @pytest.mark.asyncio
    async def test_memcached_getsetdel(self, aiomcache_pool, memcached_cache):
        N = 10000
        aiomcache_total_time = 0
        for n in range(N):
            start = time.time()
            await aiomcache_pool.set(b"hi", b"value")
            await aiomcache_pool.get(b"hi")
            await aiomcache_pool.delete(b"hi")
            aiomcache_total_time += time.time() - start

        aiocache_total_time = 0
        for n in range(N):
            start = time.time()
            await memcached_cache.set("hi", "value", timeout=0)
            await memcached_cache.get("hi", timeout=0)
            await memcached_cache.delete("hi", timeout=0)
            aiocache_total_time += time.time() - start

        print("\n{:0.2f}/{:0.2f}: {:0.2f}".format(
            aiocache_total_time, aiomcache_total_time, aiocache_total_time/aiomcache_total_time))
        print("aiocache avg call: {:0.5f}s".format(
            aiocache_total_time/N))
        print("aiomcache avg call: {:0.5f}s".format(
            aiomcache_total_time/N))
        assert aiocache_total_time/aiomcache_total_time < 1.30

    @pytest.mark.asyncio
    async def test_memcached_multigetsetdel(self, aiomcache_pool, memcached_cache):
        N = 2000
        aiomcache_total_time = 0
        values = [b"a", b"b", b"c", b"d", b"e", b"f"]
        for n in range(N):
            start = time.time()
            for k in values:
                await aiomcache_pool.set(k, k)
            await aiomcache_pool.multi_get(*values)
            for k in values:
                await aiomcache_pool.delete(k)
            aiomcache_total_time += time.time() - start

        aiocache_total_time = 0
        values = [b"a", b"b", b"c", b"d", b"e", b"f"]
        for n in range(N):
            start = time.time()
            await memcached_cache.multi_set([(x, x) for x in values], timeout=0)
            await memcached_cache.multi_get(values, timeout=0)
            for k in values:
                await memcached_cache.delete(k, timeout=0)
            aiocache_total_time += time.time() - start

        print("\n{:0.2f}/{:0.2f}: {:0.2f}".format(
            aiocache_total_time, aiomcache_total_time, aiocache_total_time/aiomcache_total_time))
        print("aiocache avg call: {:0.5f}s".format(
            aiocache_total_time/N))
        print("aiomcache avg call: {:0.5f}s".format(
            aiomcache_total_time/N))
        assert aiocache_total_time/aiomcache_total_time < 1.90
