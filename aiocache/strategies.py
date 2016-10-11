import abc
import logging

from collections import deque


logger = logging.getLogger(__name__)


class BaseStrategy(metaclass=abc.ABCMeta):

    async def pre_get(self):
        pass

    async def post_get(self):
        pass

    async def pre_set(self):
        pass

    async def post_set(self):
        pass

    async def pre_mget(self):
        pass

    async def post_mget(self):
        pass

    async def pre_mset(self):
        pass

    async def post_mset(self):
        pass


class LRUStrategy(BaseStrategy):
    """
    Implement a Least Recently Used strategy with max_keys. The strategy does the following:

        - When a key is retrieved (get or mget), keys are moved to the beginning of the queue
        - When a key is added (set, mset or add), keys are added to the beginning of the queue. If
            the queue is full, it will remove as many keys as needed to make space for the new
            ones.
    """

    def __init__(self, client, max_keys=1):
        assert max_keys >= 1, "Number of keys must be 1 or bigger"
        self.dq = deque(maxlen=max_keys)
        self.client = client

    async def post_get(self, key, value):
        self.dq.remove(key)
        self.dq.appendleft()

    async def pre_set(self, key, value):
        if len(self.dq) == self.dq.maxlen:
            await self.client.delete(self.dq.pop())
