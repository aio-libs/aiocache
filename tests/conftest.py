import pytest


@pytest.fixture()
def max_conns():
    return None


@pytest.fixture()
def decode_responses():
    return False


@pytest.fixture
async def valkey_client(max_conns, decode_responses):
    from glide import GlideClient, GlideClientConfiguration, NodeAddress

    addresses = [NodeAddress("localhost", 6379)]
    conf = GlideClientConfiguration(addresses=addresses, database_id=0)
    client = await GlideClient.create(conf)

    yield client

    await client.close()
