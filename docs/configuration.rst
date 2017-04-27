..  _configuration:

Configuration
=============

Cache aliases
-------------

The settings module allows to setup cache configurations and then use them with the specified alias. To set the config, call ``settings.set_config``:

.. automethod:: aiocache.settings.set_config

To retrieve a copy of the current config, you can use ``settings.get_config``.


Next snippet shows an example usage:

.. literalinclude:: ../examples/cached_alias_config.py
  :language: python
  :linenos:
  :emphasize-lines: 6-26

When you do ``caches.get('alias_name')``, the cache instance is built lazily. Next accesses will return the **same** instance. If instead of reusing the same instance, you need a new one every time, use ``caches.create('alias_name')``.
