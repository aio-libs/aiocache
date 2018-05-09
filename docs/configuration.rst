..  _configuration:

Configuration
=============

Cache aliases
-------------

The caches module allows to setup cache configurations and then use them either using an alias or retrieving the config explicitly. To set the config, use property ``caches.config`` like in example below.
To retrieve a copy of the current config, you can use ``caches.config`` or ``caches.get_alias_config`` for an alias config.


Next snippet shows an example usage:

.. literalinclude:: ../examples/cached_alias_config.py
  :language: python
  :linenos:
  :emphasize-lines: 6-26

When you do ``caches.get('alias_name')``, the cache instance is built lazily the first time. Next accesses will return the **same** instance. If instead of reusing the same instance, you need a new one every time, use ``caches.create('alias_name')``. One of the advantages of ``caches.create`` is that it accepts extra args that then are passed to the cache constructor. This way you can override args like namespace, endpoint, etc.

.. automodule:: aiocache.factory
   :members:

