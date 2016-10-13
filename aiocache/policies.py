import logging

from collections import deque


logger = logging.getLogger(__name__)


class DefaultPolicy:
    """
    Default and base policy. It's the default used by all backends and it does nothing.

    :param client: Backend class to interact with the storage.
    """

    def __init__(self, client):
        self.client = client

    async def pre_get(self, key):
        pass

    async def post_get(self, key):
        pass

    async def pre_set(self, key, value):
        pass

    async def post_set(self, key, value):
        pass


class LRUPolicy(DefaultPolicy):
    """
    Implements a Least Recently Used policy with max_keys. The policy does the following:

        - When a key is retrieved (get or mget), keys are moved to the beginning of the queue
        - When a key is added (set, mset or add), keys are added to the beginning of the queue. If
            the queue is full, it will remove as many keys as needed to make space for the new
            ones.
    """
    def __init__(self, *args, max_keys=None, **kwargs):
        super().__init__(*args, **kwargs)
        if max_keys is not None:
            assert max_keys >= 1, "Number of keys must be 1 or bigger"
        self.dq = deque(maxlen=max_keys)

    async def post_get(self, key):
        """
        Remove the key from its current position and set it at the beginning of the queue.

        :param key: string key used in the get operation
        """
        self.dq.remove(key)
        self.dq.appendleft(key)

    async def post_set(self, key, value):
        """
        Set the given key at the beginning of the queue. If the queue is full, remove the last
        item first.

        :param key: string key used in the set operation
        :param value: obj used in the set operation
        """
        if len(self.dq) == self.dq.maxlen:
            await self.client.delete(self.dq.pop())
        self.dq.appendleft(key)
