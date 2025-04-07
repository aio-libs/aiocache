import pytest


@pytest.fixture()
def max_conns():
    return None


@pytest.fixture()
def decode_responses():
    return False


@pytest.fixture
def valkey_config():
    from glide import GlideClientConfiguration, NodeAddress

    addresses = [NodeAddress("localhost", 6379)]
    conf = GlideClientConfiguration(addresses=addresses, database_id=0)

    yield conf


@pytest.fixture
async def valkey_client(max_conns, decode_responses, valkey_config):
    from glide import GlideClient

    client = await GlideClient.create(valkey_config)

    yield client

    await client.close()
