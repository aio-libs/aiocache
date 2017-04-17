import pytest

from collections import namedtuple

from aiocache.serializers import DefaultSerializer, PickleSerializer, JsonSerializer


Dummy = namedtuple("Dummy", "a, b")


class TestDefaultSerializer:

    @pytest.mark.parametrize("obj", [
        1, True, ["1", 1], {"key": "value"}, Dummy(1, 2)])
    def test_set_types(self, obj):
        with pytest.raises(TypeError):
            DefaultSerializer().dumps(obj)

    def test_dumps(self):
        assert DefaultSerializer().dumps("hi") == "hi"

    def test_loads(self):
        assert DefaultSerializer().loads("hi") == "hi"


class TestPickleSerializer:

    def test_dumps(self):
        assert PickleSerializer().dumps("hi") == b'\x80\x03X\x02\x00\x00\x00hiq\x00.'

    def test_dumps_with_none(self):
        assert isinstance(PickleSerializer().dumps(None), bytes)

    def test_loads(self):
        assert PickleSerializer().loads(b'\x80\x03X\x02\x00\x00\x00hiq\x00.') == "hi"

    def test_loads_with_none(self):
        assert PickleSerializer().loads(None) is None

    def test_dumps_and_loads(self):
        obj = Dummy(1, 2)
        serializer = PickleSerializer()
        assert serializer.loads(serializer.dumps(obj)) == obj


class TestJsonSerializer:

    def test_dumps(self):
        assert (
            JsonSerializer().dumps({"hi": 1}) == '{"hi": 1}' or  # json
            JsonSerializer().dumps({"hi": 1}) == '{"hi":1}')     # ujson

    def test_dumps_with_none(self):
        assert JsonSerializer().dumps(None) == 'null'

    def test_loads_with_null(self):
        assert JsonSerializer().loads('null') is None

    def test_loads_with_none(self):
        assert JsonSerializer().loads(None) is None

    def test_dumps_and_loads(self):
        obj = {"hi": 1}
        serializer = JsonSerializer()
        assert serializer.loads(serializer.dumps(obj)) == obj
