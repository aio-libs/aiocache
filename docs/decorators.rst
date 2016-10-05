Decorators
==========

aiocache comes with a couple of decorators for caching results from asynchronous functions. Do not use the decorator in synchronous functions, it may lead to unexpected behavior.

Decorators can be used with any backend/serializer available. With that, you are able to store any python object into the desired backend:

.. literalinclude:: ../examples/decorator.py

As you may have imagined, it's very annoying to specify the backend, serializer, port and so everytime you decorate a function. For that, the ``aiocache.config_default_cache()`` utility is provided. This function will configure a global cache that will fallback any of the attributes that are not passed in the decorators. Also, you'll be able to use this default cache explicitly accessing ``aiocache.default_cache``:

.. literalinclude:: ../examples/config_default_cache.py


cached
---------------------

.. automodule:: aiocache
  :members: cached
