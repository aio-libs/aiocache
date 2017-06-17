import pytest

from aiocache import settings


class TestSettings:

    def test_settings_singleton(self):
        assert settings() is settings()

    def test_default_settings(self):
        assert settings.get_config() == {
            'default': {
                'cache': "aiocache.SimpleMemoryCache",
                'serializer': {
                    'class': "aiocache.serializers.NullSerializer"
                }
            }
        }

    def test_get_alias(self):
        assert settings.get_alias("default") == {
            'cache': "aiocache.SimpleMemoryCache",
            'serializer': {
                'class': "aiocache.serializers.NullSerializer"
            }
        }

    def test_set_empty_config(self):
        with pytest.raises(ValueError):
            settings.set_config({})

    def test_set_config_no_default(self):
        with pytest.raises(ValueError):
            settings.set_config({
                'no_default': {
                    'cache': "aiocache.RedisCache",
                    'endpoint': "127.0.0.10",
                    'port': 6378,
                    'serializer': {
                        'class': "aiocache.serializers.PickleSerializer"
                    },
                    'plugins': [
                        {'class': "aiocache.plugins.HitMissRatioPlugin"},
                        {'class': "aiocache.plugins.TimingPlugin"}
                    ]
                }
            })
