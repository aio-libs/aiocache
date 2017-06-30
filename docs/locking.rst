..  _locking:

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
