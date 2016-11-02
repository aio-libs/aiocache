from aiocache.serializers import PickleSerializer, JsonSerializer


class TestPickleSerializer:

    def test_loads_with_none(self):
        assert PickleSerializer().loads(None) is None


class TestJsonSerializer:

    def test_loads_with_none(self):
        assert JsonSerializer().loads(None) is None
