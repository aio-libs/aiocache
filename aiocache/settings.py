from aiocache import caches
from aiocache.log import logger


class settings:

    __instance = None
    _config = {
        'default': {
            'cache': "aiocache.SimpleMemoryCache",
            'serializer': {
                'class': "aiocache.serializers.StringSerializer"
            }
        }
    }

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    @classmethod
    def get_alias(cls, alias):
        logger.warning("Deprecated, please use 'aiocache.caches.get_config[alias]'")
        return caches.get_alias_config(alias)

    @classmethod
    def get_config(cls):
        logger.warning("Deprecated, please use 'aiocache.caches.get_config'")
        return caches.get_config()

    @classmethod
    def set_config(cls, config):
        logger.warning("Deprecated, please use 'aiocache.caches.get_config'")
        return caches.set_config(config)
