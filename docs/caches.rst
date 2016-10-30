..  _caches:

Caches
======

You can use different caches according to your needs. All the caches implement the same interface which includes the methods: ``add``, ``get``, ``set``, ``multi_get``, ``multi_set``, ``delete``, ``exists``, ``raw``. If you feel a method is really missing here do not hesitate to open an issue in github.

Caches are always working through a serializer. The serializer allows to transform the data when storing and retrieving the data from the storage. This for example, allows to store python classes in Redis which by default, it only supports storing bytes. As you may have guessed, this has a con: in some cases the data won't be raw accessible in the storage as the serializer may apply some weird transformations on it before storing it. To give an idea, the set operation on any backend works as follows:

.. image:: images/set_operation_flow.png
  :align: center

Let's go with a more specific case. Let's pick Redis as the cache with namespace "test" and PickleSerializer as the serializer:

#. We receive a set("key", "value")
#. "key" will become "test:key" when applying the ``build_key``
#. "value" will become an array of bytes when calling ``serializer.dumps``

..  _basecache:

BaseCache
---------

.. autoclass:: aiocache.cache.BaseCache
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
