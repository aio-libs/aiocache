import pytest

from asynctest import Mock

from aiocache.cache import BaseCache
from aiocache.policies import LRUPolicy


@pytest.fixture
def lru_policy():
    return LRUPolicy(max_keys=10)


class TestLRUPolicy:

    def test_setup(self, lru_policy):
        assert lru_policy.deque.maxlen == 10

        with pytest.raises(AssertionError):
            LRUPolicy(max_keys=0)

    @pytest.mark.asyncio
    async def test_post_get(self, lru_policy):
        lru_policy.deque.appendleft(pytest.KEY)
        lru_policy.deque.appendleft(pytest.KEY_1)

        await lru_policy.post_get(Mock(spec=BaseCache), pytest.KEY)

        assert lru_policy.deque.index(pytest.KEY) == 0

    @pytest.mark.asyncio
    async def test_post_set(self, lru_policy):
        await lru_policy.post_set(Mock(spec=BaseCache), pytest.KEY, "value")

        assert lru_policy.deque.index(pytest.KEY) == 0

    @pytest.mark.asyncio
    async def test_post_set_full(self, lru_policy):
        lru_policy.deque.extend(range(1, 11))
        await lru_policy.post_set(Mock(spec=BaseCache), pytest.KEY, "value")

        lru_policy.client.delete.assert_called_with(10)
        assert lru_policy.deque.index(pytest.KEY) == 0
        assert lru_policy.deque.index(1) == 1
        assert len(lru_policy.deque) == 10
