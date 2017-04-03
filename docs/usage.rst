Installation and Usage
======================


Installing
----------

You just need to do a ``pip install aiocache``.


Caches
------

Configuring and using a cache is as simple as

.. code-block:: python

    >>> import asyncio
    >>> loop = asyncio.get_event_loop()
    >>> from aiocache import SimpleMemoryCache
    >>> cache = SimpleMemoryCache()
    >>> loop.run_until_complete(cache.set('key', 'value'))
    True
    >>> loop.run_until_complete(cache.get('key'))
    'value'

Here we are using the :ref:`simplememorycache` but you can use any other listed in :ref:`caches`. All caches contain the same minimum interface which consists on the following functions:

  - ``add``: Only adds key/value if key does not exist. Otherwise raises ValueError.
  - ``get``: Retrieve value identified by key.
  - ``set``: Sets key/value.
  - ``multi_get``: Retrieves multiple key/values.
  - ``multi_set``: Sets multiple key/values.
  - ``exists``: Returns True if key exists False otherwise.
  - ``delete``: Deletes key and returns number of deleted items.
  - ``clear``: Clears the items stored.
  - ``raw``: Executes the specified command using the underlying client.


Configuring project default settings
------------------------------------

  DISCLAIMER: The following utilities are using a globals-like anti pattern. If your project has an approach for dependency injection or using singletons use them please.

Sometimes you just want to use the same settings all over your project. To do so, some helpers are provided like ``set_defaults``, ``set_default_serializer``, ``set_default_plugins``:

.. automodule:: aiocache.settings
  :members: set_defaults, set_default_serializer, set_default_plugins

If you have many custom settings that you want to configure globally, it can be tedious to pick all of them from config file and forward them to the shown helpers. For these cases, the ``set_from_dict`` can give you a hand:

.. automodule:: aiocache.settings
  :members: set_from_dict

If you need to know the current default configuration for your project, you can always use the ``get_defaults`` as

.. code-block:: python

    >>> import pprint
    >>> import aiocache
    >>> pprint.pprint(aiocache.settings.get_defaults())
    {'DEFAULT_CACHE': <class 'aiocache.cache.SimpleMemoryCache'>,
     'DEFAULT_CACHE_KWARGS': {},
     'DEFAULT_PLUGINS': {},
     'DEFAULT_SERIALIZER': <class 'aiocache.serializers.DefaultSerializer'>,
     'DEFAULT_SERIALIZER_KWARGS': {}}


Decorators
----------

aiocache provides :ref:`cached` and :ref:`multi_cached` decorators. The first one can be used to cache function calls or single values returned by the function. The second one can be used to cache dictionaries returned by the function call. For more information, visit the :ref:`decorators` reference.
