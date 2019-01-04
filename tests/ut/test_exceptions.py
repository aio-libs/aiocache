from aiocache.exceptions import InvalidCacheType


def test_inherit_from_exception():
    assert isinstance(InvalidCacheType(), Exception)
