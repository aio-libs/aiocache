import msgpack
import pytest
try:
    import ujson as json
except ImportError:
    import json

from collections import namedtuple

from aiocache.serializers import NullSerializer, StringSerializer, PickleSerializer, JsonSerializer


Dummy = namedtuple("Dummy", "a, b")

TYPES = [1, 2.0, "hi", True, ["1", 1], {"key": "value"}, Dummy(1, 2)]


class TestNullSerializer:
    @pytest.mark.parametrize("obj", TYPES)
    def test_set_types(self, obj):
        assert NullSerializer().dumps(obj) is obj

    def test_loads(self):
        assert NullSerializer().loads("hi") is "hi"


class TestStringSerializer:

    @pytest.mark.parametrize("obj", TYPES)
    def test_set_types(self, obj):
        assert StringSerializer().dumps(obj) == str(obj)

    def test_loads(self):
        assert StringSerializer().loads("hi") == "hi"


class TestPickleSerializer:

    @pytest.mark.parametrize("obj", TYPES)
    def test_set_types(self, obj):
        serializer = PickleSerializer()
        assert serializer.loads(serializer.dumps(obj)) == obj

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

    @pytest.mark.parametrize("obj", TYPES)
    def test_set_types(self, obj):
        assert JsonSerializer().dumps(obj) == json.dumps(obj)

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


class TestMessagePackSerializer:

    @pytest.mark.parametrize("obj", TYPES)
    def test_set_types(self, obj):
        serializer = MessagePackSerializer()
        assert serializer.loads(serializer.dumps(obj)) == obj

    def test_dumps(self):
        assert MessagePackSerializer().dumps("hi") == b'\x80\x03X\x02\x00\x00\x00hiq\x00.'

    def test_dumps_with_none(self):
        assert isinstance(MessagePackSerializer().dumps(None), bytes)

    def test_loads(self):
        assert MessagePackSerializer().loads(b'\x80\x03X\x02\x00\x00\x00hiq\x00.') == "hi"

    def test_loads_with_none(self):
        assert MessagePackSerializer().loads(None) is None

    def test_dumps_and_loads(self):
        obj = Dummy(1, 2)
        serializer = MessagePackSerializer()
        assert serializer.loads(serializer.dumps(obj)) == obj
