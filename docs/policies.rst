..  _policies:

Policies
========

Policies can be used to change the behavior of the cache. By default any backend uses :class:`aiocache.policies.DefaultPolicy` which does nothing. You can select the policy with::

    >>> from aiocache import SimpleMemoryCache
    >>> from aiocache.policies import LRUPolicy
    cache = SimpleMemoryCache()
    cache.set_policy(LRUPolicy, max_keys=1000)

In case the current policies are not covering your needs, you can always define your custom policy by inheriting from `DefaultPolicy`_ and overriding the needed methods.

..  _defaultpolicy:

DefaultPolicy
-------------

.. autoclass:: aiocache.policies.DefaultPolicy
  :members:
  :undoc-members:

..  _lrupolicy:

LRUPolicy
---------

.. autoclass:: aiocache.policies.LRUPolicy
  :members:
  :undoc-members:


An example usage of the policy:

.. literalinclude:: ../examples/policy.py
  :language: python
  :linenos:
