import pytest
import asyncio
import asynctest


class TestMockCache:
    """
    This class ensures that all backends behave the same way at logic level. It tries to ensure
    the calls to the necessary methods like serialization and strategies are performed when needed.
    To add a new backend just create the fixture for the new backend and add id as a param for the
    cache fixture
    """

    @pytest.mark.asyncio
    async def test_get(self, mock_cache):
        await mock_cache.get(pytest.KEY)

        assert mock_cache.serializer.loads.call_count == 1
        assert mock_cache._build_key.call_count == 1
        assert mock_cache.policy.pre_get.call_count == 1
        assert mock_cache.policy.post_get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_timeouts(self, mock_cache):
        mock_cache._backend.get = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.get(pytest.KEY)

    @pytest.mark.asyncio
    async def test_set(self, mock_cache):
        await mock_cache.set(pytest.KEY, "value")

        assert mock_cache.serializer.dumps.call_count == 1
        assert mock_cache._build_key.call_count == 1
        assert mock_cache.policy.pre_set.call_count == 1
        assert mock_cache.policy.post_set.call_count == 1

    @pytest.mark.asyncio
    async def test_set_timeouts(self, mock_cache):
        mock_cache._backend.set = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.set(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_add(self, mock_cache):
        mock_cache._backend.exists.return_value = False
        await mock_cache.add(pytest.KEY, "value")

        assert mock_cache.serializer.dumps.call_count == 1
        assert mock_cache._build_key.call_count == 1
        assert mock_cache.policy.pre_set.call_count == 1
        assert mock_cache.policy.post_set.call_count == 1

    @pytest.mark.asyncio
    async def test_add_timeouts(self, mock_cache):
        mock_cache._backend.add = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.add(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_mget(self, mock_cache):
        await mock_cache.multi_get([pytest.KEY, pytest.KEY_1])

        assert mock_cache.serializer.loads.call_count == 2
        assert mock_cache._build_key.call_count == 2
        assert mock_cache.policy.pre_get.call_count == 2
        assert mock_cache.policy.post_get.call_count == 2

    @pytest.mark.asyncio
    async def test_mget_timeouts(self, mock_cache):
        mock_cache._backend.multi_get = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.multi_get(pytest.KEY, "value")

    @pytest.mark.asyncio
    async def test_mset(self, mock_cache):
        await mock_cache.multi_set([[pytest.KEY, "value"], [pytest.KEY_1, "value1"]])

        assert mock_cache.serializer.dumps.call_count == 2
        assert mock_cache._build_key.call_count == 2
        assert mock_cache.policy.pre_set.call_count == 2
        assert mock_cache.policy.post_set.call_count == 2

    @pytest.mark.asyncio
    async def test_mset_timeouts(self, mock_cache):
        mock_cache._backend.multi_set = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.multi_set([[pytest.KEY, "value"], [pytest.KEY_1, "value1"]])

    @pytest.mark.asyncio
    async def test_exists(self, mock_cache):
        await mock_cache.exists(pytest.KEY)

        assert mock_cache._build_key.call_count == 1

    @pytest.mark.asyncio
    async def test_exists_timeouts(self, mock_cache):
        mock_cache._backend.exists = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.exists(pytest.KEY)

    @pytest.mark.asyncio
    async def test_delete(self, mock_cache):
        await mock_cache.delete(pytest.KEY)

        assert mock_cache._build_key.call_count == 1

    @pytest.mark.asyncio
    async def test_delete_timeouts(self, mock_cache):
        mock_cache._backend.delete = asynctest.CoroutineMock(side_effect=asyncio.sleep(0.005))

        with pytest.raises(asyncio.TimeoutError):
            await mock_cache.delete(pytest.KEY)

    @pytest.mark.parametrize("namespace, expected", (
        [None, "test" + pytest.KEY],
        ["", pytest.KEY],
        ["my_ns", "my_ns" + pytest.KEY],)
    )
    def test_build_key(self, mock_cache, namespace, expected):
        assert mock_cache._build_key(pytest.KEY, namespace=namespace) == expected


class TestRedisCache:
    @pytest.mark.parametrize("namespace, expected", (
        [None, "test:" + pytest.KEY],
        ["", pytest.KEY],
        ["my_ns", "my_ns:" + pytest.KEY],)
    )
    def test_build_key(self, redis_cache, namespace, expected):
        assert redis_cache._build_key(pytest.KEY, namespace=namespace) == expected
