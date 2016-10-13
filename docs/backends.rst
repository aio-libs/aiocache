Backends
========

You can use different backends according to your needs. All the backends implement the same interface which includes the methods: ``add``, ``get``, ``set``, ``multi_get``, ``multi_set``, ``delete``, ``exists``. If you feel a method is really missing here do not hesitate to open an issue in github.

Backends are always working through a serializer. The serializer allows to transform the data when storing and retrieving the data from the storage. This for example, allows to store python classes in Redis which by default, it only supports storing strings, int, bytes. As you may have guessed, this has a con: in some cases the data won't be raw accessible in the storage as the serializer may apply some weird transformations on it before storing it. To give an idea, the set operation on any backend works as follows:

.. image:: images/set_operation_flow.png

Now let's go with a more specific case. Let's pick Redis as the backend with namespace "test", PickleSerializer as the backend serializer:

#. We receive a set("key", "value")
#. "key" will become "test:key" when applying the ``build_key``
#. "value" will become an array of bytes when calling ``serializer.serialize``

BaseCache
---------

.. autoclass:: aiocache.backends.base.BaseCache
  :members:

RedisCache
----------

.. autoclass:: aiocache.RedisCache
  :members:
  :undoc-members:


SimpleMemoryCache
-----------------

.. autoclass:: aiocache.SimpleMemoryCache
  :members:
  :undoc-members:
