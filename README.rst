aiocache
========

.. image:: https://travis-ci.org/argaen/aiocache.svg?branch=master
  :target: https://travis-ci.org/argaen/aiocache

.. image:: https://codecov.io/gh/argaen/aiocache/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/argaen/aiocache

.. image:: https://badge.fury.io/py/aiocache.svg
  :target: https://pypi.python.org/pypi/aiocache

Disclaimer: The code is still in alpha version so if use it under your own responsibility.

An asynchronous cache implementation with multiple backends for asyncio. Used `django-redis-cache <https://github.com/sebleier/django-redis-cache>`_ and `redis-simple-cache <https://github.com/vivekn/redis-simple-cache>`_ as inspiration for the initial structure.

Current implementations are:

- SimpleMemoryCache
- RedisCache using aioredis_
- MemCache using aiomcache_ IN PROGRESS


All the interfaces implement at least ``get``, ``set`` and ``delete`` operations. Some of them may implement extra logic like ``ttl`` in RedisCache. However, this package is not meant for fine grained control over the objects you store in the cache (like updating/incrementing specific fields from your object) as it aims for simplicity. By doing that, it's possible to store any python object into any of the backends.

Features
--------

- SimpleMemoryCache: A simple cache implementation in memory. Note that functions are async there to keep compatibility with other backend implementations.
- RedisCache: Cache implementation using aioredis_.
- MemCache: Cache implementation using aiomcache_. IN PROGRESS
- cached decorator for async functions. IN PROGRESS

Usage
-----

First, you need to install the package with ``pip install aiocache``.

cached decorator
~~~~~~~~~~~~~~~~

The typical use is to decorate function calls that interact with some external resource. You can do this easily with the ``cached`` decorator:

.. code-block:: python

  import asyncio

  from collections import namedtuple

  from aiocache import cached, RedisCache
  from aiocache.serializers import PickleSerializer

  Result = namedtuple('Result', "content, status")


  @cached(ttl=10)
  async def async_main():
      print("First ASYNC non cached call...")
      await asyncio.sleep(1)
      return Result("content", 200)


  if __name__ == "__main__":
      loop = asyncio.get_event_loop()
      print(loop.run_until_complete(async_main()))
      print(loop.run_until_complete(async_main()))
      print(loop.run_until_complete(async_main()))
      print(loop.run_until_complete(async_main()))

The decorator by default will use the ``SimpleMemoryCache`` backend and the ``DefaultSerializer``. If you want to use a different backend, you can call it with ``cached(ttl=10, backend=RedisCache)``. Also, if you want to use a specific serializer just use ``cached(ttl=10, serializer=DefaultSerializer())``

Sometimes, you will want to use this decorator with specific backend and serializer and explicitly doing that in every decorator doesn't follow the Do not Repeat Yourself principle. This is why the ``config_default_cache`` is provided. This configures a global cache that can be imported from anywhere in your code:

.. code-block:: python

  import asyncio
  import aiocache

  from collections import namedtuple

  from aiocache import cached

  Result = namedtuple('Result', "content, status")

  aiocache.config_default_cache()

  async def global_cache():
      await aiocache.default_cache.set("key", "value")
      await asyncio.sleep(1)
      return await aiocache.default_cache.get("key")


  @cached(ttl=10, namespace="test")
  async def decorator_example():
      print("First ASYNC non cached call...")
      await asyncio.sleep(1)
      return Result("content", 200)


  if __name__ == "__main__":
      loop = asyncio.get_event_loop()
      print(loop.run_until_complete(global_cache()))
      print(loop.run_until_complete(decorator_example()))
      print(loop.run_until_complete(decorator_example()))
      print(loop.run_until_complete(decorator_example()))

So, the decorator resolves the cache to use as follows:

#. If a backend is passed, use that one.
#. If there is no backend but a default_cache exists (populated with ``aiocache.config_default_cache``) it will use that one.
#. If any of the previous happened, use the SimpleMemoryCache with DefaultSerializer (if serializer is passed, it will use that one).

Also in some cases, some backends like the RedisCache, may need extra arguments like ``endpoint`` or ``port``. You can also pass them in the ``aiocache.config_default_cache`` or in the ``cached`` decorator.

Backends and serializers
~~~~~~~~~~~~~~~~~~~~~

Sometimes you need to explicitly instantiate a cache class and interact with it. You can do it as follows:


.. code-block:: python

  import asyncio

  from aiocache import RedisCache


  async def main():
      cache = RedisCache(endpoint="127.0.0.1", port=6379, namespace="main")
      await cache.set("key", "value")
      await cache.set("expire_me", "value", ttl=10)  # Key will expire after 10 secs
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
