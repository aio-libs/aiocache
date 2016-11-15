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
  - ``clear``: Clears the items stored.
  - ``raw``: Executes the specified command using the underlying client.


Cache components
----------------

Each cache instance has three main components:
  - **backend**: Is the client that connects the cache with the client that talks with the desired backend (Redis, Memcached, etc...).
  - **serializer**: It transforms the value when saving and retrieving. This allows to save complex Python objects, change format of the data stored, etc. :ref:`defaultserializer` is used by default if not specified during instantiation time. Check :ref:`serializers` for a list of available serializers. If the functionality you need is not covered, you can write your custom serializer.
  - **policy**: It ensures the chosen cache policy is followed. By default it uses :ref:`defaultpolicy` but you can set any other calling ``cache.policy = MyNewPolicy()``. Check :ref:`policies` for a list of available policies. If the functionality you need is not covered, you can write your custom policy.


.. image:: images/architecture.png
  :align: center


Configuring a project settings
------------------------------

Sometimes you just want to use the same settings all over your project. To do so, some helpers are provided like ``set_defaults``, ``set_default_serializer``, ``set_default_policy``:

.. automodule:: aiocache.settings
  :members: set_defaults, set_default_serializer, set_default_policy

If you have many custom settings that you want to configure globally, it can be tedious to pick all of them from config file and forward them to the shown helpers. For these cases, the ``set_from_dict`` can give you a hand:

.. automodule:: aiocache.settings
  :members: set_from_dict

If you need to know the currently configure defaults for your projects, you can always use the ``get_defaults`` as

.. code-block:: python

    >>> import pprint
    >>> import aiocache
    >>> aiocache.settings.get_defaults()
    >>> pprint.pprint(aiocache.settings.get_defaults())
    {'DEFAULT_CACHE': <class 'aiocache.cache.SimpleMemoryCache'>,
     'DEFAULT_CACHE_KWARGS': {},
     'DEFAULT_POLICY': <class 'aiocache.policies.DefaultPolicy'>,
     'DEFAULT_POLICY_KWARGS': {},
     'DEFAULT_SERIALIZER': <class 'aiocache.serializers.DefaultSerializer'>,
     'DEFAULT_SERIALIZER_KWARGS': {}}


Decorators
----------

aiocache provides :ref:`cached` and :ref:`multi_cached` decorators. The first one can be used to cache function calls or single values returned by the function. The second one can be used to cache dictionaries returned by the function call. For more information, visit the :ref:`decorators` reference.
