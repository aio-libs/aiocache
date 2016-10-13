import logging

from collections import deque


logger = logging.getLogger(__name__)


class DefaultPolicy:

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
    Implement a Least Recently Used policy with max_keys. The policy does the following:

        - When a key is retrieved (get or mget), keys are moved to the beginning of the queue
        - When a key is added (set, mset or add), keys are added to the beginning of the queue. If
            the queue is full, it will remove as many keys as needed to make space for the new
            ones.
    """

    def __init__(self, max_keys=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert max_keys >= 1, "Number of keys must be 1 or bigger"
        self.dq = deque(maxlen=max_keys)

    async def post_get(self, key):
        self.dq.remove(key)
        self.dq.appendleft()

    async def pre_set(self, key, value):
        if len(self.dq) == self.dq.maxlen:
            await self.client.delete(self.dq.pop())
