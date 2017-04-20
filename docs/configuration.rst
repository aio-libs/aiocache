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


Cache classes defaults
----------------------

In some cases you won't be using aliases but explicit instances of the classes. You can change the defaults the classes are using with its respective ``set_defaults``:

.. literalinclude:: ../examples/config_default_cache.py
  :language: python
  :linenos:
  :emphasize-lines: 10-14

You can set back the original defaults by calling ``set_defaults`` without arguments.

You can override any attribute supported by the class. You can check those in :ref:`caches` reference.
