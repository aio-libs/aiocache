Decorators
==========

aiocache comes with a couple of decorators for caching results from asynchronous functions. Do not use the decorator in synchronous functions, it may lead to unexpected behavior.

cached
------

.. automodule:: aiocache
  :members: cached

The decorator can be used with any backend/serializer available. With that, you are able to store any python object into the desired backend:

.. literalinclude:: ../examples/decorator.py
  :language: python
  :linenos:

multi_cached
------------

.. automodule:: aiocache
  :members: multi_cached
