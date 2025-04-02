from unittest.mock import ANY, AsyncMock, create_autospec, patch

import pytest

from glide import Transaction, Script
from glide.exceptions import RequestError

from aiocache.backends.valkey import ValkeyBackend, ValkeyCache
from aiocache.base import BaseCache
from aiocache.serializers import JsonSerializer
from ...utils import Keys, ensure_key


@pytest.fixture
def valkey(valkey_client):
    valkey = ValkeyBackend(client=valkey_client)
    with patch.object(valkey, "client", autospec=True) as m:
        # These methods actually return an awaitable.
        for method in (
            "eval",
            "expire",
            "get",
            "execute_command",
            "exists",
            "incrby",
            "persist",
            "delete",
            "scan",
            "flushdb",
        ):
            setattr(m, method, AsyncMock(return_value=None, spec_set=()))
        m.mget = AsyncMock(return_value=[None], spec_set=())
        m.set = AsyncMock(return_value=True, spec_set=())

        yield valkey


class TestValkeyBackend:
    # async def test_valkey_backend_requires_client_decode_responses(self, valkey_client):
    #     with pytest.raises(ValueError) as ve:
    #         ValkeyBackend(client=valkey_client)
    #
    #     assert str(ve.value) == (
    #         "valkey client must be constructed with decode_responses set to False"
    #     )

    async def test_get(self, valkey):
        valkey.client.get.return_value = b"value"
        assert await valkey._get(Keys.KEY) == "value"
        valkey.client.get.assert_called_with(Keys.KEY)

    async def test_gets(self, mocker, valkey):
        mocker.spy(valkey, "_get")
        await valkey._gets(Keys.KEY)
        valkey._get.assert_called_with(Keys.KEY, encoding="utf-8", _conn=ANY)

    async def test_set(self, valkey):
        await valkey._set(Keys.KEY, "value")
        valkey.client.set.assert_called_with(Keys.KEY, "value")

        await valkey._set(Keys.KEY, "value", ttl=1)
        valkey.client.set.assert_called_once

    async def test_set_cas_token(self, mocker, valkey):
        mocker.spy(valkey, "_cas")
        await valkey._set(Keys.KEY, "value", _cas_token="old_value", _conn=valkey.client)
        valkey._cas.assert_called_with(
            Keys.KEY, "value", "old_value", ttl=None, _conn=valkey.client
        )

    async def test_cas(self, mocker, valkey):
        mocker.spy(valkey, "_script")
        await valkey._cas(Keys.KEY, "value", "old_value", ttl=10, _conn=valkey.client)
        valkey._script.assert_called_with(
            valkey.CAS_SCRIPT,
            *[[Keys.KEY], "value", "old_value", "EX", "10"],
        )

    async def test_cas_float_ttl(self, mocker, valkey):
        mocker.spy(valkey, "_script")
        await valkey._cas(Keys.KEY, "value", "old_value", ttl=0.1, _conn=valkey.client)
        valkey._script.assert_called_with(
            valkey.CAS_SCRIPT,
            *[[Keys.KEY], "value", "old_value", "PX", "100"],
        )

    async def test_multi_get(self, valkey):
        await valkey._multi_get([Keys.KEY, Keys.KEY_1])
        valkey.client.mget.assert_called_with(Keys.KEY, Keys.KEY_1)

    async def test_multi_set(self, valkey):
        await valkey._multi_set([(Keys.KEY, "value"), (Keys.KEY_1, "random")])
        valkey.client.mset.assert_called_with({Keys.KEY: "value", Keys.KEY_1: "random"})

    async def test_multi_set_with_ttl(self, valkey, mocker):
        spy_mset = mocker.spy(Transaction, "mset")
        spy_expire = mocker.spy(Transaction, "expire")
        await valkey._multi_set([(Keys.KEY, "value"), (Keys.KEY_1, "random")], ttl=1)

        valkey.client.exec.assert_called()

        assert spy_mset.call_count == 1
        assert spy_expire.call_count == 2
        spy_expire.assert_any_call(valkey.client.exec.call_args.args[0], Keys.KEY, 1)
        spy_expire.assert_any_call(valkey.client.exec.call_args.args[0], Keys.KEY_1, 1)

    async def test_add(self, valkey):
        await valkey._add(Keys.KEY, "value")
        valkey.client.set.assert_called_with(Keys.KEY, "value", nx=True, ex=None)

        await valkey._add(Keys.KEY, "value", 1)
        valkey.client.set.assert_called_with(Keys.KEY, "value", nx=True, ex=1)

    async def test_add_existing(self, valkey):
        valkey.client.set.return_value = False
        with pytest.raises(ValueError):
            await valkey._add(Keys.KEY, "value")

    async def test_add_float_ttl(self, valkey):
        await valkey._add(Keys.KEY, "value", 0.1)
        valkey.client.set.assert_called_with(Keys.KEY, "value", nx=True, px=100)

    async def test_exists(self, valkey):
        valkey.client.exists.return_value = 1
        await valkey._exists(Keys.KEY)
        valkey.client.exists.assert_called_with([Keys.KEY])

    async def test_increment(self, valkey):
        await valkey._increment(Keys.KEY, delta=2)
        valkey.client.incrby.assert_called_with(Keys.KEY, 2)

    async def test_increment_typerror(self, valkey):
        valkey.client.incrby.side_effect = RequestError("msg")
        with pytest.raises(TypeError):
            await valkey._increment(Keys.KEY, delta=2)
        valkey.client.incrby.assert_called_with(Keys.KEY, 2)

    async def test_expire(self, valkey):
        await valkey._expire(Keys.KEY, 1)
        valkey.client.expire.assert_called_with(Keys.KEY, 1)
        await valkey._increment(Keys.KEY, 2)

    async def test_expire_0_ttl(self, valkey):
        await valkey._expire(Keys.KEY, ttl=0)
        valkey.client.persist.assert_called_with(Keys.KEY)

    async def test_delete(self, valkey):
        await valkey._delete(Keys.KEY)
        valkey.client.delete.assert_called_with([Keys.KEY])

    async def test_clear(self, valkey):
        valkey.client.scan.return_value = [b"0", ["nm:a", "nm:b"]]
        await valkey._clear("nm")
        valkey.client.delete.assert_called_with("nm:a", "nm:b")

    async def test_clear_no_keys(self, valkey):
        valkey.client.scan.return_value = [b"0", []]
        await valkey._clear("nm")
        valkey.client.delete.assert_not_called()

    async def test_clear_no_namespace(self, valkey):
        await valkey._clear()
        assert valkey.client.flushdb.call_count == 1

    async def test_script(self, valkey):
        script = Script("server.call('get', Keys[1]")
        await valkey._script(script, Keys.KEY)
        valkey.client.invoke_script.assert_called_with(script, Keys.KEY, ())

    async def test_redlock_release(self, mocker, valkey):
        mocker.spy(valkey, "_script")
        await valkey._redlock_release(Keys.KEY, "random")
        valkey._script.assert_called_with(valkey.RELEASE_SCRIPT, Keys.KEY, "random")


class TestValkeyCache:
    @pytest.fixture
    def set_test_namespace(self, valkey_cache):
        valkey_cache.namespace = "test"
        yield
        valkey_cache.namespace = None

    def test_name(self):
        assert ValkeyCache.NAME == "valkey"

    def test_inheritance(self, valkey_client):
        assert isinstance(ValkeyCache(client=valkey_client), BaseCache)

    def test_default_serializer(self, valkey_client):
        assert isinstance(ValkeyCache(client=valkey_client).serializer, JsonSerializer)

    @pytest.mark.parametrize(
        "path,expected", [("", {}), ("/", {}), ("/1", {"db": "1"}), ("/1/2/3", {"db": "1"})]
    )
    def test_parse_uri_path(self, path, expected, valkey_client):
        assert ValkeyCache(client=valkey_client).parse_uri_path(path) == expected

    @pytest.mark.parametrize(
        "namespace, expected",
        (
            [None, "test:" + ensure_key(Keys.KEY)],
            ["", ensure_key(Keys.KEY)],
            ["my_ns", "my_ns:" + ensure_key(Keys.KEY)],
        ),  # noqa: B950
    )
    def test_build_key_double_dot(self, set_test_namespace, valkey_cache, namespace, expected):
        assert valkey_cache.build_key(Keys.KEY, namespace) == expected

    def test_build_key_no_namespace(self, valkey_cache):
        assert valkey_cache.build_key(Keys.KEY, namespace=None) == Keys.KEY
