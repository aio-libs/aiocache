..  _plugins:

Plugins
=======

Plugins can be used to change the behavior of the cache. By default all caches are configured without any plugin but can add new ones in the constructor or after initializing the cache class::

    >>> from aiocache import SimpleMemoryCache
    >>> from aiocache.plugins import TimingPlugin
    cache = SimpleMemoryCache(plugins=[HitMissRatioPlugin()])
    cache.plugins += [TimingPlugin()]

You can define your custom plugin by inheriting from `BasePlugin`_ and overriding the needed methods. All commands have a ``pre`` and a ``post`` hooks.

An complete example of using the plugins:

.. literalinclude:: ../examples/plugins.py
  :language: python
  :linenos:


..  _baseplugin:

BasePlugin
----------

.. autoclass:: aiocache.plugins.BasePlugin
  :members:
  :undoc-members:

..  _timingplugin:

TimingPlugin
------------

.. autoclass:: aiocache.plugins.TimingPlugin
  :members:
  :undoc-members:

..  _hitmissratioplugin:

HitMissRatioPlugin
------------------

.. autoclass:: aiocache.plugins.HitMissRatioPlugin
  :members:
  :undoc-members:
