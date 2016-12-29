import pytest

from aiocache import settings, RedisCache, SimpleMemoryCache
from aiocache.backends import RedisBackend


@pytest.fixture
def set_settings():
    settings.DEFAULT_CACHE_KWARGS = {
        'endpoint': "endpoint",
        'port': "port",
        'password': "pass",
        'db': 2
    }
    settings.DEFAULT_CACHE = RedisCache
    yield
    settings.DEFAULT_CACHE = SimpleMemoryCache
    settings.DEFAULT_CACHE_KWARGS = {}


class TestRedisBackend:

    def test_setup(self):
        redis_backend = RedisBackend()
        assert redis_backend.endpoint == "127.0.0.1"
        assert redis_backend.port == 6379
        assert redis_backend.db == 0
        assert redis_backend.password is None

    def test_setup_override(self):
        redis_backend = RedisBackend(
            db=2,
            password="pass")

        assert redis_backend.endpoint == "127.0.0.1"
        assert redis_backend.port == 6379
        assert redis_backend.db == 2
        assert redis_backend.password == "pass"

    def test_setup_default_settings(self, set_settings):
        redis_backend = RedisBackend()

        assert redis_backend.endpoint == "endpoint"
        assert redis_backend.port == "port"
        assert redis_backend.db == 2
        assert redis_backend.password == "pass"

    def test_setup_default_settings_kwargs_override(self, set_settings):
        redis_backend = RedisBackend(
            endpoint="a",
            port=123,
            db=1)

        assert redis_backend.endpoint == "a"
        assert redis_backend.port == 123
        assert redis_backend.db == 1
        assert redis_backend.password == "pass"

    def test_setup_default_ignored_wrong_class(self, set_settings):
        settings.DEFAULT_CACHE = str

        redis_backend = RedisBackend()
        assert redis_backend.endpoint == "127.0.0.1"
        assert redis_backend.port == 6379
        assert redis_backend.db == 0
        assert redis_backend.password is None
