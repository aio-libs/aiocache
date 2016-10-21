..  _serializers:

Serializers
===========

Serializers can be attached to backends in order to serialize/deserialize data sent and retrieved from the backend. To use a specific serializer::

    >>> from aiocache import SimpleMemoryCache
    >>> from aiocache.serializers import PickleSerializer
    cache = SimpleMemoryCache(serializer=PickleSerializer())

In case the current serializers are not covering your needs, you can always define your custom serializer by inheriting from `DefaultSerializer`_ and overriding the needed methods.

..  _defaultserializer:

DefaultSerializer
-----------------

.. autoclass:: aiocache.serializers.DefaultSerializer
  :members:
  :undoc-members: serialize, deserialize

..  _pickleserializer:

PickleSerializer
----------------

.. autoclass:: aiocache.serializers.PickleSerializer
  :members:

..  _jsonserializer:

JsonSerializer
--------------

.. autoclass:: aiocache.serializers.JsonSerializer
  :members:
