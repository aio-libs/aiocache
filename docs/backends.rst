..  _backends:

Backends
========

Backends are the components that talk with the clients that connect to the needed backend. For example, :ref:`RedisBackend` talks with aioredis. Backends are not meant to be used by themselves unless you **only** want to interact directly with the backend.

..  _redisbackend:

RedisBackend
------------

.. autoclass:: aiocache.backends.redis.RedisCache
  :members:


..  _simplememorybackend:

SimpleMemoryBackend
-------------------

.. autoclass:: aiocache.backends.memory.SimpleMemoryCache
  :members:


..  _memcachedbackend:

MemcachedBackend
----------------

.. autoclass:: aiocache.backends.memcached.MemcachedCache
  :members:
