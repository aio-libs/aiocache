Installation and Usage
======================


Installing
----------

Do ``pip install aiocache``.


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


Decorators
----------

aiocache provides :ref:`cached` and :ref:`multi_cached` decorators. The first one can be used to cache function calls or single values returned by the function. The second one can be used to cache dictionaries returned by the function call. For more information, visit the :ref:`decorators` reference.
