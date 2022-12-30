Testing
=======

It's really easy to cut the dependency with aiocache functionality:

..  literalinclude:: ../examples/testing.py

Note that we are passing the :ref:`basecache` as the spec for the Mock.

Also, for debuging purposes you can use `AIOCACHE_DISABLE = 1 python myscript.py` to disable caching.
