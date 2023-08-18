import pytest
import redis.asyncio as redis


@pytest.fixture()
def max_conns():
    return None


@pytest.fixture
async def redis_client(max_conns):
    r = redis.Redis(
        host="127.0.0.1",
        port=6379,
        db=0,
        password=None,
        decode_responses=False,
        socket_connect_timeout=None,
        max_connections=max_conns
    )
    yield r
    await r.close()
