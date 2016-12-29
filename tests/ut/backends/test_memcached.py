import pytest

from aiocache import settings, MemcachedCache, SimpleMemoryCache
from aiocache.backends import MemcachedBackend


@pytest.fixture
def set_settings():
    settings.DEFAULT_CACHE_KWARGS = {
        'endpoint': "endpoint",
        'port': "port",
    }
    settings.DEFAULT_CACHE = MemcachedCache
    yield
    settings.DEFAULT_CACHE = SimpleMemoryCache
    settings.DEFAULT_CACHE_KWARGS = {}


class TestMemcachedBackend:

    def test_setup(self):
        redis_backend = MemcachedBackend()
        assert redis_backend.endpoint == "127.0.0.1"
        assert redis_backend.port == 11211

    def test_setup_override(self):
        redis_backend = MemcachedBackend(
            endpoint="127.0.0.2",
            port=2)

        assert redis_backend.endpoint == "127.0.0.2"
        assert redis_backend.port == 2

    def test_setup_default_settings(self, set_settings):
        redis_backend = MemcachedBackend()

        assert redis_backend.endpoint == "endpoint"
        assert redis_backend.port == "port"

    def test_setup_default_settings_kwargs_override(self, set_settings):
        redis_backend = MemcachedBackend(
            endpoint="a")

        assert redis_backend.endpoint == "a"
        assert redis_backend.port == "port"

    def test_setup_default_ignored_wrong_class(self, set_settings):
        settings.DEFAULT_CACHE = str

        redis_backend = MemcachedBackend()
        assert redis_backend.endpoint == "127.0.0.1"
        assert redis_backend.port == 11211
