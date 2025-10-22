..  _decorators:

Decorators
==========

aiocache comes with a couple of decorators for caching results from asynchronous functions. Do not use the decorator in synchronous functions, it may lead to unexpected behavior.

..  _cached:

cached
------

.. automodule:: aiocache
  :members: cached

.. literalinclude:: ../examples/cached_decorator.py
  :language: python
  :linenos:

The ``@cached`` decorator returns a wrapper object that exposes cache control methods, such as ``.refresh()`` and ``.invalidate()``. Use ``.refresh()`` to force a cache refresh for the given arguments, bypassing the cache.

**Example:**

.. code-block:: python

   @cached()
   async def compute(x):
       return x * 2

   await compute(1)         # Uses cache if available
   await compute.refresh(1) # Forces refresh, updates cache

   await compute.invalidate()    # Invalidate all cache keys
   await compute.invalidate(key) # Invalidate a specific cache key

..  _multi_cached:

multi_cached
------------

.. automodule:: aiocache
  :members: multi_cached

.. literalinclude:: ../examples/multicached_decorator.py
  :language: python
  :linenos:
