..  _caches:

Caches
======

You can use different caches according to your needs. All the caches implement the same interface.

Caches are always working together with a serializer which transforms data when storing and retrieving from the backend. It may also contain plugins that are able to enrich the behavior of your cache (like adding metrics, logs, etc).

This is the flow of the ``set`` command:

.. image:: images/set_operation_flow.png
  :align: center

Let's go with a more specific case. Let's pick Redis as the cache with namespace "test" and PickleSerializer as the serializer:

#. We receive ``set("key", "value")``.
#. Hook ``pre_set`` of all attached plugins (none by default) is called.
#. "key" will become "test:key" when calling ``build_key``.
#. "value" will become an array of bytes when calling ``serializer.dumps`` because of ``PickleSerializer``.
#. the byte array is stored together with the key using ``set`` cmd in Redis.
#. Hook ``post_set`` of all attached plugins is called.

By default, all commands are covered by a timeout that will trigger an ``asyncio.TimeoutError`` in case of timeout. Timeout can be set at instance level or when calling the command.

The supported commands are:

  - add
  - get
  - set
  - multi_get
  - multi_set
  - delete
  - exists
  - increment
  - expire
  - clear
  - raw

If you feel a command is missing here do not hesitate to `open an issue <https://github.com/argaen/aiocache/issues>`_


..  _basecache:

BaseCache
---------

.. autoclass:: aiocache.base.BaseCache
  :members:


..  _cache:

Cache
-----

.. autoclass:: aiocache.Cache
  :members:


..  _rediscache:

RedisCache
----------

.. autoclass:: aiocache.RedisCache
  :members:


..  _simplememorycache:

SimpleMemoryCache
-----------------

.. autoclass:: aiocache.SimpleMemoryCache
  :members:


..  _memcachedcache:

MemcachedCache
--------------

.. autoclass:: aiocache.MemcachedCache
  :members:
