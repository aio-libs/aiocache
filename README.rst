aiocache
========

.. image:: https://travis-ci.org/argaen/aiocache.svg?branch=master
  :target: https://travis-ci.org/argaen/aiocache

.. image:: https://codecov.io/gh/argaen/aiocache/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/argaen/aiocache

.. image:: https://badge.fury.io/py/aiocache.svg
  :target: https://pypi.python.org/pypi/aiocache

An asynchronous cache implementation with multiple backends for asyncio. Used `django-redis-cache <https://github.com/sebleier/django-redis-cache>`_ and `redis-simple-cache <https://github.com/vivekn/redis-simple-cache>`_ as inspiration for the initial structure.

Current implementations are:

- SimpleMemoryCache
- RedisCache using aioredis_
- MemCache using aiomcache_ IN PROGRESS

The ``.get`` and ``.set`` functions provided by any of the implementations work with simple Redis ``GET/SET`` commands. This package is not meant for fine grained control over the objects you store in the cache (like updating/incrementing specific fields from your object). On the other hand, you are able to store any type of object and retrieve it back as it is.

Features
--------

- SimpleMemoryCache: A simple cache implementation in memory. Note that functions are async there to keep compatibility with other backend implementations.
- RedisCache: Cache implementation using aioredis_.
- MemCache: Cache implementation using aiomcache_. IN PROGRESS
- cached decorator for async functions. IN PROGRESS

Usage
-----

First, you need to install the package with ``pip install aiocache``. Once installed, you can try the following:

.. code-block:: python

  import asyncio

  from aiocache import RedisCache


  async def main():
      cache = RedisCache(endpoint="127.0.0.1", port=6379, namespace="main")
      await cache.set("key", "value")
      await cache.set("expire_me", "value", timeout=10)  # Key will expire after 10 secs
      print(await cache.get("key"))
      print(await cache.get("expire_me"))
      print(await cache.ttl("expire_me"))


  if __name__ == "__main__":
      loop = asyncio.get_event_loop()
      loop.run_until_complete(main())

In some cases, you may want to cache complex objects and depending on the backend, you may need to transform the data before doing that. ``aiocache`` provides a couple of serializers you can use:

.. code-block:: python

  import asyncio

  from collections import namedtuple
  from aiocache import RedisCache
  from aiocache.serializers import PickleSerializer


  MyObject = namedtuple("MyObject", ["x", "y"])


  async def main():
      cache = RedisCache(serializer=PickleSerializer(), namespace="default")
      await cache.set("key", MyObject(x=1, y=2))  # This will serialize to pickle and store in redis with bytes format
      my_object = await cache.get("key")  # This will retrieve the object and deserialize back to MyObject
      print("MyObject x={}, y={}".format(my_object.x, my_object.y))


  if __name__ == "__main__":
      loop = asyncio.get_event_loop()
      loop.run_until_complete(main())

In other cases, your serialization logic will be more advanced and you won't have enough with the default ones.  No worries, you can still pass a serializer to the constructor and also to the `get`/`set` calls. The serializer must contain the `.serialize` and `.deserialize` functions in case of using the constructor:

.. code-block:: python

  import asyncio

  from aiocache import RedisCache


  class MySerializer:
      def serialize(self, value):
          return 1

      def deserialize(self, value):
          return 2


  async def main():
      cache = RedisCache(serializer=MySerializer(), namespace="main")
      await cache.set("key", "value")  # Will use MySerializer.serialize method
      print(await cache.get("key"))  # Will use MySerializer.deserialize method


  if __name__ == "__main__":
      loop = asyncio.get_event_loop()
      loop.run_until_complete(main())

Note that the method `serialize` must return data types supported by Redis `get` operation. You can also override when using the `get` and `set` methods:

.. code-block:: python

  import asyncio

  from marshmallow import Schema, fields
  from aiocache import RedisCache


  class MyType:
      def __init__(self, x, y):
          self.x = x
          self.y = y


  class MyTypeSchema(Schema):
      x = fields.Number()
      y = fields.Number()


  def serialize(value):
      # Current implementation can't deal directly with dicts so we must cast to string
      return str(MyTypeSchema().dump(value).data)


  def deserialize(value):
      return dict(MyTypeSchema().load(value).data)


  async def main():
      cache = RedisCache(namespace="main")
      await cache.set("key", MyType(1, 2), serialize_fn=serialize)
      print(await cache.get("key", deserialize_fn=deserialize))


  if __name__ == "__main__":
      loop = asyncio.get_event_loop()
      loop.run_until_complete(main())

.. _aioredis: https://github.com/aio-libs/aioredis
.. _aiomcache: https://github.com/aio-libs/aiomcache
