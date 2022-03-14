import pickle
from collections import namedtuple
from unittest import mock

import pytest

from aiocache.serializers import (
    BaseSerializer,
    JsonSerializer,
    MsgPackSerializer,
    NullSerializer,
    PickleSerializer,
    StringSerializer,
)


Dummy = namedtuple("Dummy", "a, b")

TYPES = [1, 2.0, "hi", True, ["1", 1], {"key": "value"}, Dummy(1, 2)]
JSON_TYPES = [1, 2.0, "hi", True, ["1", 1], {"key": "value"}]


class TestBaseSerializer:
    def test_init(self):
        serializer = BaseSerializer()
        assert serializer.DEFAULT_ENCODING == "utf-8"
        assert serializer.encoding == "utf-8"

    def test_init_encoding(self):
        serializer = BaseSerializer(encoding="whatever")
        assert serializer.DEFAULT_ENCODING == "utf-8"
        assert serializer.encoding == "whatever"

    def test_dumps(self):
        with pytest.raises(NotImplementedError):
            BaseSerializer().dumps("")

    def test_loads(self):
        with pytest.raises(NotImplementedError):
            BaseSerializer().loads("")


class TestNullSerializer:
    def test_init(self):
        serializer = NullSerializer()
        assert isinstance(serializer, BaseSerializer)
        assert serializer.DEFAULT_ENCODING == "utf-8"
        assert serializer.encoding == "utf-8"

    @pytest.mark.parametrize("obj", TYPES)
    def test_set_types(self, obj):
        assert NullSerializer().dumps(obj) is obj

    def test_loads(self):
        assert NullSerializer().loads("hi") == "hi"


class TestStringSerializer:
    def test_init(self):
        serializer = StringSerializer()
        assert isinstance(serializer, BaseSerializer)
        assert serializer.DEFAULT_ENCODING == "utf-8"
        assert serializer.encoding == "utf-8"

    @pytest.mark.parametrize("obj", TYPES)
    def test_set_types(self, obj):
        assert StringSerializer().dumps(obj) == str(obj)

    def test_loads(self):
        assert StringSerializer().loads("hi") == "hi"


class TestPickleSerializer:
    @pytest.fixture
    def serializer(self):
        yield PickleSerializer(protocol=4)

    def test_init(self, serializer):
        assert isinstance(serializer, PickleSerializer)
        assert serializer.DEFAULT_ENCODING is None
        assert serializer.encoding is None
        assert serializer.protocol == 4

    def test_init_sets_default_protocol(self):
        serializer = PickleSerializer()
        assert serializer.protocol == pickle.DEFAULT_PROTOCOL

    @pytest.mark.parametrize("obj", TYPES)
    def test_set_types(self, obj, serializer):
        assert serializer.loads(serializer.dumps(obj)) == obj

    def test_dumps(self, serializer):
        expected = b"\x80\x04\x95\x06\x00\x00\x00\x00\x00\x00\x00\x8c\x02hi\x94."
        assert serializer.dumps("hi") == expected

    def test_dumps_with_none(self, serializer):
        assert isinstance(serializer.dumps(None), bytes)

    def test_loads(self, serializer):
        assert serializer.loads(b"\x80\x03X\x02\x00\x00\x00hiq\x00.") == "hi"

    def test_loads_with_none(self, serializer):
        assert serializer.loads(None) is None

    def test_dumps_and_loads(self, serializer):
        obj = Dummy(1, 2)
        assert serializer.loads(serializer.dumps(obj)) == obj


class TestJsonSerializer:
    def test_init(self):
        serializer = JsonSerializer()
        assert isinstance(serializer, BaseSerializer)
        assert serializer.DEFAULT_ENCODING == "utf-8"
        assert serializer.encoding == "utf-8"

    @pytest.mark.parametrize("obj", JSON_TYPES)
    def test_set_types(self, obj):
        serializer = JsonSerializer()
        assert serializer.loads(serializer.dumps(obj)) == obj

    def test_dumps(self):
        assert (
            JsonSerializer().dumps({"hi": 1}) == '{"hi": 1}'
            or JsonSerializer().dumps({"hi": 1}) == '{"hi":1}'  # json
        )  # ujson

    def test_dumps_with_none(self):
        assert JsonSerializer().dumps(None) == "null"

    def test_loads_with_null(self):
        assert JsonSerializer().loads("null") is None

    def test_loads_with_none(self):
        assert JsonSerializer().loads(None) is None

    def test_dumps_and_loads(self):
        obj = {"hi": 1}
        serializer = JsonSerializer()
        assert serializer.loads(serializer.dumps(obj)) == obj


class TestMsgPackSerializer:
    def test_init(self):
        serializer = MsgPackSerializer()
        assert isinstance(serializer, BaseSerializer)
        assert serializer.DEFAULT_ENCODING == "utf-8"
        assert serializer.encoding == "utf-8"

    def test_init_fails_if_msgpack_not_installed(self):
        with mock.patch("aiocache.serializers.serializers.msgpack", None):
            with pytest.raises(RuntimeError):
                MsgPackSerializer()
            assert JsonSerializer(), "Other serializers should still initialize"

    def test_init_use_list(self):
        serializer = MsgPackSerializer(use_list=True)
        assert serializer.use_list is True

    @pytest.mark.parametrize("obj", JSON_TYPES)
    def test_set_types(self, obj):
        serializer = MsgPackSerializer()
        assert serializer.loads(serializer.dumps(obj)) == obj

    def test_dumps(self):
        assert MsgPackSerializer().dumps("hi") == b"\xa2hi"

    def test_dumps_with_none(self):
        assert isinstance(MsgPackSerializer().dumps(None), bytes)

    def test_loads(self):
        assert MsgPackSerializer().loads(b"\xa2hi") == "hi"

    def test_loads_no_encoding(self):
        assert MsgPackSerializer(encoding=None).loads(b"\xa2hi") == b"hi"

    def test_loads_with_none(self):
        assert MsgPackSerializer().loads(None) is None

    def test_dumps_and_loads_tuple(self):
        serializer = MsgPackSerializer()
        assert serializer.loads(serializer.dumps(Dummy(1, 2))) == [1, 2]

    def test_dumps_and_loads_dict(self):
        serializer = MsgPackSerializer()
        d = {"a": [1, 2, ("1", 2)], "b": {"b": 1, "c": [1, 2]}}
        assert serializer.loads(serializer.dumps(d)) == {
            "a": [1, 2, ["1", 2]],
            "b": {"b": 1, "c": [1, 2]},
        }
