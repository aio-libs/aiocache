Usage
=====

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
  - ``raw``: Executes the specified command using the underlying client.


Cache components
----------------

Each cache instance has three main components:
  - **backend**: Is the client that connects the cache with the client that talks with the desired backend (Redis, Memcached, etc...).
  - **serializer**: It transforms the value when saving and retrieving. This allows to save complex Python objects, change format of the data stored, etc. :ref:`defaultserializer` is used by default if not specified during instantiation time. Check :ref:`serializers` for a list of available serializers. If the functionality you need is not covered, you can write your custom serializer.
  - **policy**: It ensures the chosen cache policy is followed. By default it uses :ref:`defaultpolicy` but you can set any other calling ``cache.set_policy($policy)``. Check :ref:`policies` for a list of available policies. If the functionality you need is not covered, you can write your custom policy.


.. image:: docs/images/architecture.png
  :align: center


Configuring a project cache
---------------------------

Sometimes you just want to use the same cache over all your project or at least, have a default one for common usage. You can configure a global one with:


.. code-block:: python

  import aiocache
  from aiocache.serializers import PickleSerializer
  from aiocache.policies import LRUPolicy

  aiocache.config_default_cache(
    backend=aiocache.RedisCache,
    serializer=PickleSerializer(),
    policy=LRUPolicy(max_keys=1000),
    endpoint=127.0.0.1,
    port=6379)

Once done, everytime you use any of the :ref:`decorators`, if an explicit backend isn't passed, they will use the default one. Also, if you want the explicit cache, you can do a ``from aiocache import default_cache as cache`` and start using it (after configuring it).


Decorators
----------

aiocache provides :ref:`cached` and :ref:`multi_cached` decorators. The first one can be used to cache function calls or single values returned by the function. The second one can be used to cache dictionaries returned by the function call. For more information, visit the :ref:`decorators` reference.
