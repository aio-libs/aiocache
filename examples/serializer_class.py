import asyncio
import zlib

from glide import GlideClientConfiguration, NodeAddress

from aiocache import ValkeyCache
from aiocache.serializers import BaseSerializer

addresses = [NodeAddress("localhost", 6379)]
config = GlideClientConfiguration(addresses=addresses, database_id=0)


class CompressionSerializer(BaseSerializer):

    # This is needed because zlib works with bytes.
    # this way the underlying backend knows how to
    # store/retrieve values
    DEFAULT_ENCODING = None

    def dumps(self, value):
        print("I've received:\n{}".format(value))
        compressed = zlib.compress(value.encode())
        print("But I'm storing:\n{}".format(compressed))
        return compressed

    def loads(self, value):
        print("I've retrieved:\n{}".format(value))
        decompressed = zlib.decompress(value).decode()
        print("But I'm returning:\n{}".format(decompressed))
        return decompressed


async def serializer():
    text = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt"
        "ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation"
        "ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in"
        "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur"
        "sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit"
        "anim id est laborum."
    )
    async with ValkeyCache(
        config=config, namespace="main", serializer=CompressionSerializer()
    ) as cache:
        await cache.set("key", text)
        print("-----------------------------------")
        real_value = await cache.get("key")
        compressed_value = await cache.raw("get", "main:key")
    assert len(compressed_value) < len(real_value.encode())


async def test_serializer():
    await serializer()
    async with ValkeyCache(
        config=config, namespace="main", serializer=CompressionSerializer()
    ) as cache:
        await cache.delete("key")
        await cache.close()


if __name__ == "__main__":
    asyncio.run(test_serializer())
