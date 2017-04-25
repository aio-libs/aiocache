..  _configuration:

Configuration
=============

Cache aliases
-------------

The settings module allows to setup different cache configurations and then use them with the specified alias. To set the config, call ``settings.set_config``:

.. automethod:: aiocache.settings.set_config

To retrieve a copy of the current config, you can use ``settings.get_config``.


Next snippet shows an example usage:

.. literalinclude:: ../examples/cached_alias_config.py
  :language: python
  :linenos:
  :emphasize-lines: 6-26

Those are the fallbacks for args:

- From ``set_config``.
- From cache class defaults.

When you access an alias with ``caches['default']``, the cache instance is built lazily. Next accesses will return the same instance. This also means that if after accessing it you change the config for that alias, it won't be applied.
