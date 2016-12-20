Testing
=======

It's really easy to cut the dependency with aiocache functionality:

..  literalinclude:: ../examples/testing.py

Note that we are passing the :ref:`basecache` as the spec for the Mock (you need to install ``asynctest``).

Also, for debuging purposes you can use `AIOCACHE_DISABLE = 1 python myscript.py` to disable caching. The values
returned for the different commands will be the following:

.. autoattribute:: aiocache.plugins.BasePlugin.NULL_RETURN
