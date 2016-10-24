Testing
=======

The library doesn't provide any special feature for testing but using mocks, it's really easy to cut the dependency with aiocache functionality:

..  literalinclude:: ../examples/testing.py

Note that we are passing the :ref:`basecache` as the spec for the CoroutineMock (you need to install ``asynctest``).
