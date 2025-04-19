aiocache
########

Asyncio cache supporting multiple backends (memory, redis, memcached, dynamodb).

.. image:: https://codecov.io/gh/aio-libs/aiocache/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/aio-libs/aiocache

.. image:: https://badge.fury.io/py/aiocache.svg
  :target: https://pypi.python.org/pypi/aiocache

.. image:: https://img.shields.io/pypi/pyversions/aiocache.svg
  :target: https://pypi.python.org/pypi/aiocache

This library aims for simplicity over specialization. All caches contain the same minimum interface which consists on the following functions:

- ``add``: Only adds key/value if key does not exist.
- ``get``: Retrieve value identified by key.
- ``set``: Sets key/value.
- ``multi_get``: Retrieves multiple key/values.
- ``multi_set``: Sets multiple key/values.
- ``exists``: Returns True if key exists False otherwise.
- ``increment``: Increment the value stored in the given key.
- ``delete``: Deletes key and returns number of deleted items.
- ``clear``: Clears the items stored.
- ``raw``: Executes the specified command using the underlying client.


.. role:: python(code)
  :language: python

.. contents::

.. section-numbering:


Installing
==========

- ``pip install aiocache``
- ``pip install aiocache[redis]``
- ``pip install aiocache[memcached]``
- ``pip install aiocache[redis,memcached]``
- ``pip install aiocache[msgpack]``


Usage
=====

Using a cache is as simple as

.. code-block:: python

    >>> import asyncio
    >>> from aiocache import SimpleMemoryCache
    >>> cache = SimpleMemoryCache()  # Or RedisCache, MemcachedCache...
    >>> with asyncio.Runner() as runner:
    >>>     runner.run(cache.set('key', 'value'))
    True
    >>>     runner.run(cache.get('key'))
    'value'

Or as a decorator

.. code-block:: python

    import asyncio

    from collections import namedtuple

    from aiocache import RedisCache, cached
    from aiocache.serializers import PickleSerializer
    # With this we can store python objects in backends like Redis!

    Result = namedtuple('Result', "content, status")
    redis_client = redis.Redis(host="127.0.0.1", port=6379)
    redis_cache = RedisCache(redis_client, namespace="main")


    @cached(redis_cache, key="key", serializer=PickleSerializer(), port=6379, namespace="main")
    async def cached_call():
        print("Sleeping for three seconds zzzz.....")
        await asyncio.sleep(3)
        return Result("content", 200)


    async def run():
        async with redis_client, redis_cache:
            await cached_call()
            await cached_call()
            await cached_call()
            await redis_cache.delete("key")

    if __name__ == "__main__":
        asyncio.run(run())


How does it work
================

Aiocache provides 3 main entities:

- **backends**: Allow you specify which backend you want to use for your cache. Currently supporting: SimpleMemoryCache, RedisCache using redis_, MemCache using aiomcache_ and DynamoDB using aiobotocore_ (available on aiocache-dynamodb_).
- **serializers**: Serialize and deserialize the data between your code and the backends. This allows you to save any Python object into your cache. Currently supporting: StringSerializer, PickleSerializer, JsonSerializer, and MsgPackSerializer. But you can also build custom ones.
- **plugins**: Implement a hooks system that allows to execute extra behavior before and after of each command.

 If you are missing an implementation of backend, serializer or plugin you think it could be interesting for the package, do not hesitate to open a new issue.

.. image:: docs/images/architecture.png
  :align: center

Those 3 entities combine during some of the cache operations to apply the desired command (backend), data transformation (serializer) and pre/post hooks (plugins). To have a better vision of what happens, here you can check how ``set`` function works in ``aiocache``:

.. image:: docs/images/set_operation_flow.png
  :align: center


Amazing examples
================

In `examples folder <https://github.com/argaen/aiocache/tree/master/examples>`_ you can check different use cases:

- `Sanic, Aiohttp and Tornado <https://github.com/argaen/aiocache/tree/master/examples/frameworks>`_
- `Python object in Redis <https://github.com/argaen/aiocache/blob/master/examples/python_object.py>`_
- `Custom serializer for compressing data <https://github.com/argaen/aiocache/blob/master/examples/serializer_class.py>`_
- `TimingPlugin and HitMissRatioPlugin demos <https://github.com/argaen/aiocache/blob/master/examples/plugins.py>`_
- `Using marshmallow as a serializer <https://github.com/argaen/aiocache/blob/master/examples/marshmallow_serializer_class.py>`_
- `Using cached decorator <https://github.com/argaen/aiocache/blob/master/examples/cached_decorator.py>`_.
- `Using multi_cached decorator <https://github.com/argaen/aiocache/blob/master/examples/multicached_decorator.py>`_.



Documentation
=============

- `Usage <http://aiocache.readthedocs.io/en/latest>`_
- `Caches <http://aiocache.readthedocs.io/en/latest/caches.html>`_
- `Serializers <http://aiocache.readthedocs.io/en/latest/serializers.html>`_
- `Plugins <http://aiocache.readthedocs.io/en/latest/plugins.html>`_
- `Configuration <http://aiocache.readthedocs.io/en/latest/configuration.html>`_
- `Decorators <http://aiocache.readthedocs.io/en/latest/decorators.html>`_
- `Testing <http://aiocache.readthedocs.io/en/latest/testing.html>`_
- `Examples <https://github.com/argaen/aiocache/tree/master/examples>`_


.. _redis: https://github.com/redis/redis-py
.. _aiomcache: https://github.com/aio-libs/aiomcache
.. _aiobotocore: https://github.com/aio-libs/aiobotocore
.. _aiocache-dynamodb: https://github.com/vonsteer/aiobotocore
