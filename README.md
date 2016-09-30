# aiocache

A cache implementation in multiple backends for asyncio. Used
 [django-redis-cache](https://github.com/sebleier/django-redis-cache) and
 [redis-simple-cache](https://github.com/vivekn/redis-simple-cache)
as inspiration for the initial structure.

## Usage

First, you need to install the package with `pip install aiocache`. Once installed, you can try the
following:

```python
from aiocache import RedisCache

cache = RedisCache(endpoint="127.0.0.1", port=6379, namespace="test")
await cache.set("key", "value")
await cache.set("expire_me", "value", timeout=10) # Key will expire after 10 secs
```

In some cases, you may want to cache complex objects and depending on the backend, you may need to
transform the data before doing that. `aiocache` provides a couple of serializers you can use:

```python
from collections import namedtuple
from aiocache import RedisCache
from aiocache.serializers import PickleSerializer

MyObject = namedtuple("MyObject", ["x", "y"])

cache = RedisCache(serializer=PickleSerializer())
await cache.set("key", MyObject(x=1, y=2))  # This will serialize to pickle and store in redis with bytes format
my_object = await cache.get("key")  # This will retrieve the object and deserialize back to MyObject
assert my_object.x == 1
```

In other cases, your serialization logic will be more advanced and you won't have enough with the default ones.
No worries, you can still pass a serializer to the constructor and also to the `get`/`set` calls. The serializer
must contain the `.serialize` and `.deserialize` functions in case of using the constructor:

```python
from aiocache import RedisCache

class MySerializer:
  def serialize(self, value):
    return 1

  def deserialize(self, value):
    return 2

cache=RedisCache(serializer=MySerializer())
await cache.set("key", "value")  # Will use MySerializer.serialize method
await cache.get("key")  # Will use MySerializer.deserialize method
```

Note that the method `serialize` must return data types supported by Redis `get` operation. You can also override
when using the `get` and `set` methods:

```python
from marshmallow import Schema, fields
from aiocache import RedisCache

class MyType:
  def __init__(self, x, y):
    self.x = x
    self.y = y

class MyTypeSchema:
  x = fields.Number()
  y = fields.Number()

cache=RedisCache()
await cache.set("key", MyType(1, 2), serialize_fn=MyTypeSchema.dumps)
await cache.get("key", deserialize_fn=MyTypeSchema.loads)
```


### Supported backends

- Redis: [aioredis](https://github.com/aio-libs/aioredis)
- Memcached: [aiomcache](https://github.com/aio-libs/aiomcache) IN PROGRESS
