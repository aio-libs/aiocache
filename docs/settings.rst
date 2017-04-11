..  _settings:

Settings
========

Sometimes you just want to use the same settings all over your project. To do so, some helpers are provided like ``set_cache``, ``set_serializer``, ``set_plugins``.

All cache instances and decorators use the settings modules to pull values in case they are not passed explicitly. For example, imagine you do the following:

.. code-block:: python

    >>> from aiocache import settings, RedisCache
    >>> settings.set_cache(RedisCache, endpoint="127.0.0.1")
    >>> RedisCache(port=123)
    RedisCache (127.0.0.1:123)
    >>> RedisCache(endpoint="192.168.1.10", port=8379)
    RedisCache (192.168.1.10:8379)

Now let's see a case where behavior may be unexpected and see why it behaves this way:

.. code-block:: python

  >>> from aiocache import MemcachedCache, RedisCache, settings
  2017-04-12 23:34:39,115 WARNING aiocache.log(13) | cPickle module not found, using pickle
  >>> settings.set_cache(RedisCache, endpoint="192.168.1.10", port=8379)
  >>> MemcachedCache()
  MemcachedCache (127.0.0.1:11211)

In the previous code, the default endpoint and port are not applied when creating the ``MemcachedCache`` instance because the default cache is a ``RedisCache`` and the defaults only apply if the class being instantiated is that class or a subclass.

.. automodule:: aiocache.settings
  :members: set_cache, set_serializer, set_plugins

If you have many custom settings that you want to configure globally, it can be tedious to pick all of them from config file and forward them to the shown helpers. For these cases, the ``set_config`` can be useful:

.. automodule:: aiocache.settings
  :members: set_config

If you need to know the current default configuration for aiocache, use ``get_defaults`` as

.. code-block:: python

    >>> import pprint
    >>> from aiocache import settings
    >>> pprint.pprint(settings.get_defaults())
    {'CACHE': <class 'aiocache.cache.SimpleMemoryCache'>,
     'CACHE_KWARGS': {},
     'PLUGINS': {},
     'SERIALIZER': <class 'aiocache.serializers.DefaultSerializer'>,
     'SERIALIZER_KWARGS': {}}
