import asyncio

from glide import GlideClientConfiguration, NodeAddress

from aiocache import ValkeyCache

addresses = [NodeAddress("localhost", 6379)]
config = GlideClientConfiguration(addresses=addresses, database_id=0)


async def valkey():
    async with ValkeyCache(config=config, namespace="main") as cache:
        await cache.set("key", "value")
        await cache.set("expire_me", "value", ttl=10)

        assert await cache.get("key") == "value"
        assert await cache.get("expire_me") == "value"
        assert await cache.raw("ttl", "main:expire_me") > 0


async def test_valkey():
    await valkey()
    async with ValkeyCache(config=config, namespace="main") as cache:
        await cache.delete("key")
        await cache.delete("expire_me")
        await cache.close()


if __name__ == "__main__":
    asyncio.run(test_valkey())
