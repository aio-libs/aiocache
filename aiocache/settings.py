from copy import deepcopy


class settings:

    __instance = None
    _config = {
        'default': {
            'cache': "aiocache.SimpleMemoryCache",
            'serializer': {
                'class': "aiocache.serializers.DefaultSerializer"
            }
        }
    }

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    @classmethod
    def get_alias(cls, alias):
        return cls._config[alias]

    @classmethod
    def get_config(cls):
        """
        Return copy of current stored config
        """
        return deepcopy(cls._config)

    @classmethod
    def set_config(cls, config):
        """
        Set (override) the default settings for aiocache from a dict-like structure.
        The structure is the following::

            {
                'default': {
                    'cache': "aiocache.SimpleMemoryCache",
                    'serializer': {
                        'class': "aiocache.serializers.DefaultSerializer"
                    }
                },
                'redis_alt': {
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
            }

        'default' key must always exist when passing a new config. Default configuration
        is::

            {
                'default': {
                    'cache': "aiocache.SimpleMemoryCache",
                    'serializer': {
                        'class': "aiocache.serializers.DefaultSerializer"
                    }
                }
            }

        You can set your own classes there.
        The class params accept both str and class types.

        All keys in the config are optional, if they are not passed the defaults
        for the specified class will be used.
        """
        if "default" not in config:
            raise ValueError("default config must be provided")
        cls._config = config
