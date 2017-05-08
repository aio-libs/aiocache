import asyncio

from collections import deque
from aiocache import RedisCache
from aiocache.plugins import BasePlugin


class LRUPlugin(BasePlugin):
    """
    Implements a Least Recently Used policy with max_keys. The policy does the following:
        - When a key is retrieved get, keys are moved to the beginning of the queue
        - When a key is added (set), keys are added to the beginning of the queue. If
            the queue is full, it will remove as many keys as needed to make space for the new
            ones.
    IMPORTANT!
        - The queue is implemented using a Python deque so it is NOT persistent!
        - Careful when working on distributed systems, you may run into incosistencies if this
            policy is run from different instances that point to the same endpoint and namespace.
        - To have a full LRU, you should also implement the add, multi_set and multi_get methods.
    """
    def __init__(self, max_keys=None):
        super().__init__()
        if max_keys is not None:
            assert max_keys >= 1, "Number of keys must be 1 or bigger"
        self.deque = deque(maxlen=max_keys)

    async def post_get(self, client, key, *args, took=0, **kwargs):
        """
        Remove the key from its current position and set it at the beginning of the queue.
        :param key: string key used in the get operation
        :param client: :class:`aiocache.base.BaseCache` or child instance to use to interact with
            the storage if needed
        """
        if await client.exists(key):
            self.deque.remove(key)
            self.deque.appendleft(key)

    async def post_set(self, client, key, value, *args, took=0, **kwargs):
        """
        Set the given key at the beginning of the queue. If the queue is full, remove the last
        item first.
        :param key: string key used in the set operation
        :param value: obj used in the set operation
        :param client: :class:`aiocache.base.BaseCache` or child instance to use to interact with
            the storage if needed
        """
        if len(self.deque) == self.deque.maxlen:
            await client.delete(self.deque.pop())
        self.deque.appendleft(key)


cache = RedisCache(
    endpoint="127.0.0.1",
    port=6379,
    plugins=[LRUPlugin(max_keys=2)],
    namespace="main")


async def redis():
    await cache.set("key", "value")
    await cache.set("key_1", "value")
    await cache.set("key_2", "value")

    assert await cache.get("key") is None
    assert await cache.get("key_1") == "value"
    assert await cache.get("key_2") == "value"
    assert len(await cache.raw("keys", "{}:*".format(cache.namespace))) == 2


def test_redis():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(redis())
    loop.run_until_complete(cache.delete("key"))
    loop.run_until_complete(cache.delete("key_1"))
    loop.run_until_complete(cache.delete("key_2"))


if __name__ == "__main__":
    test_redis()
