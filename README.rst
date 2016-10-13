aiocache
========

.. image:: https://travis-ci.org/argaen/aiocache.svg?branch=master
  :target: https://travis-ci.org/argaen/aiocache

.. image:: https://codecov.io/gh/argaen/aiocache/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/argaen/aiocache

.. image:: https://badge.fury.io/py/aiocache.svg
  :target: https://pypi.python.org/pypi/aiocache

An asynchronous cache implementation with multiple backends for asyncio. Used `django-redis-cache <https://github.com/sebleier/django-redis-cache>`_ and `redis-simple-cache <https://github.com/vivekn/redis-simple-cache>`_ as inspiration for the initial structure.

Disclaimer: The code is still in **alpha** version so new versions may introduce breaking changes. Once version 1.0 is reached, deprecation policy will be introduced.

Current supported backends are:

- SimpleMemoryCache
- RedisCache using aioredis_
- MemCache using aiomcache_ IN PROGRESS


This libraries aims for simplicity over specialization. It provides a common interface for all caches which allows to store any python object. The operations supported by all backends are:

- ``add``
- ``exists``
- ``get``
- ``set``
- ``multi_get``
- ``multi_set``
- ``delete``


Usage
-----

Install the package with ``pip install aiocache``.

cached decorator
~~~~~~~~~~~~~~~~

The typical use case is to decorate function calls that interact with some external resource. You can do this easily with the ``cached`` decorator:

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


  @cached(ttl=10, namespace="test:")
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
~~~~~~~~~~~~~~~~~~~~~~~~

You can instantiate a cache class and interact with it as follows:


.. code-block:: python

  import asyncio

  from aiocache import RedisCache


  async def main():
      cache = RedisCache(endpoint="127.0.0.1", port=6379, namespace="main:")
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
      cache = RedisCache(serializer=PickleSerializer(), namespace="default:")
      await cache.set("key", MyObject(x=1, y=2))  # This will serialize to pickle and store in redis with bytes format
      my_object = await cache.get("key")  # This will retrieve the object and deserialize back to MyObject
      print("MyObject x={}, y={}".format(my_object.x, my_object.y))


  if __name__ == "__main__":
      loop = asyncio.get_event_loop()
      loop.run_until_complete(main())


For more examples, visit the examples folder of the project.

.. _aioredis: https://github.com/aio-libs/aioredis
.. _aiomcache: https://github.com/aio-libs/aiomcache
