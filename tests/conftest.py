import pytest
import redis.asyncio as redis


@pytest.fixture()
def max_conns():
    return None


@pytest.fixture()
def decode_responses():
    return False


@pytest.fixture
async def redis_client(max_conns, decode_responses):
    async with redis.Redis(
        host="127.0.0.1",
        port=6379,
        db=0,
        password=None,
        decode_responses=decode_responses,
        socket_connect_timeout=None,
        max_connections=max_conns
    ) as r:
        yield r
