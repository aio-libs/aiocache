..  _locking:

.. WARNING::
  This was added in version 0.7.0 and the API is new. This means its open to breaking changes in future versions until the API is considered stable.


Locking
=======


.. WARNING::
   The implementations provided are **NOT** intented for consistency/synchronization purposes. If you need a locking mechanism focused on consistency, consider implementing your mechanism based on more serious tools like https://zookeeper.apache.org/.


There are a couple of locking implementations than can help you to protect against different scenarios:


..  _redlock:

RedLock
-------

.. autoclass:: aiocache.lock.RedLock
  :members:


..  _optimisticlock:

OptimisticLock
--------------

.. autoclass:: aiocache.lock.OptimisticLock
  :members:
