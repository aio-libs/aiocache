.. aiocache documentation master file, created by
   sphinx-quickstart on Sat Oct  1 16:53:45 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to aiocache's documentation!
====================================


Installing
----------

``pip install aiocache``.

If you don't need redis or memcached support, you can install as follows:

```
AIOCACHE_REDIS=no pip install aiocache       # Don't install redis client (aioredis)
AIOCACHE_MEMCACHED=no pip install aiocache   # Don't install memcached client (aiomcache)
```


Usage
-----

Using a cache is as simple as

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
  - ``increment``: Increment the value stored in the given key.
  - ``delete``: Deletes key and returns number of deleted items.
  - ``clear``: Clears the items stored.
  - ``raw``: Executes the specified command using the underlying client.


You can also setup cache aliases like in Django settings:

.. literalinclude:: ../examples/cached_alias_config.py
  :language: python
  :linenos:
  :emphasize-lines: 6-26


In `examples folder <https://github.com/argaen/aiocache/tree/master/examples>`_ you can check different use cases:

- `Using cached decorator <https://github.com/argaen/aiocache/blob/master/examples/cached_decorator.py>`_.
- `Using multi_cached decorator <https://github.com/argaen/aiocache/blob/master/examples/multicached_decorator.py>`_.
- `Configuring cache class default args <https://github.com/argaen/aiocache/blob/master/examples/config_default_cache.py>`_
- `Simple LRU plugin for memory <https://github.com/argaen/aiocache/blob/master/examples/lru_plugin.py>`_
- `Using marshmallow as a serializer <https://github.com/argaen/aiocache/blob/master/examples/marshmallow_serializer_class.py>`_
- `TimingPlugin and HitMissRatioPlugin demos <https://github.com/argaen/aiocache/blob/master/examples/plugins.py>`_
- `Storing a python object in Redis <https://github.com/argaen/aiocache/blob/master/examples/python_object.py>`_
- `Creating a custom serializer class that compresses data <https://github.com/argaen/aiocache/blob/master/examples/serializer_class.py>`_
- `Integrations with frameworks like Sanic, Aiohttp and Tornado <https://github.com/argaen/aiocache/tree/master/examples/frameworks>`_


Contents
--------

.. toctree::

  caches
  serializers
  plugins
  configuration
  decorators
  testing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
