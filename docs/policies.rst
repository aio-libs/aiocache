Policies
========

Policies can be used to change the behavior of the cache. By default any backend uses :class:`aiocache.policies.DefaultPolicy` which does nothing. You can select the policy by calling ``cache.set_policy(MyPolicy)``.


DefaultPolicy
-------------

.. autoclass:: aiocache.policies.DefaultPolicy
  :members:
  :undoc-members:


LRUPolicy
---------

.. autoclass:: aiocache.policies.LRUPolicy
  :members:
  :undoc-members:


An example usage of the policy:

.. literalinclude:: ../examples/policy.py
  :language: python
  :linenos:
