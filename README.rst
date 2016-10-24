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

Supported backends:

- SimpleMemoryCache
- RedisCache using aioredis_
- MemCache using aiomcache_


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


Documentation
-------------

- `Usage <http://aiocache.readthedocs.io/en/latest/usage.html>`_
- `Backends <http://aiocache.readthedocs.io/en/latest/backends.html>`_
- `Serializers <http://aiocache.readthedocs.io/en/latest/serializers.html>`_
- `Policies <http://aiocache.readthedocs.io/en/latest/policies.html>`_
- `Decorators <http://aiocache.readthedocs.io/en/latest/decorators.html>`_
- `Testing <http://aiocache.readthedocs.io/en/latest/testing.html>`_
- `Examples <https://github.com/argaen/aiocache/tree/master/examples>`_


.. _aioredis: https://github.com/aio-libs/aioredis
.. _aiomcache: https://github.com/aio-libs/aiomcache
