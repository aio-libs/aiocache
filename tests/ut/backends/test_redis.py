import pytest


class TestRedisBackend:

    @pytest.mark.asyncio
    async def test_ttl(self, redis_mock_cache):
        await redis_mock_cache.ttl(pytest.KEY)

        assert redis_mock_cache._build_key.call_count == 1
