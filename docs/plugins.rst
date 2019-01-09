..  _plugins:

Plugins
=======

Plugins can be used to enrich the behavior of the cache. By default all caches are configured without any plugin but can add new ones in the constructor or after initializing the cache class::

    >>> from aiocache import Cache
    >>> from aiocache.plugins import TimingPlugin
    cache = Cache(plugins=[HitMissRatioPlugin()])
    cache.plugins += [TimingPlugin()]

You can define your custom plugin by inheriting from `BasePlugin`_ and overriding the needed methods (the overrides NEED to be async). All commands have ``pre_<command_name>`` and ``post_<command_name>`` hooks.

.. WARNING::
  Both pre and post hooks are executed awaiting the coroutine. If you perform expensive operations with the hooks, you will add more latency to the command being executed and thus, there are more probabilities of raising a timeout error. If a timeout error is raised, be aware that previous actions **won't be rolled back**.

A complete example of using plugins:

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
