import pytest


@pytest.fixture
def valkey_config():
    from glide import GlideClientConfiguration, NodeAddress

    addresses = [NodeAddress("localhost", 6379)]
    return GlideClientConfiguration(addresses=addresses, database_id=0)
