from aiocache import RedisCache


def cached(ttl=0, backend=None, serializer=None):
    cache = backend or get_default_cache(serializer=serializer)

    def cached_decorator(fn):
        async def wrapper(*args, **kwargs):
            key = fn.__module__ + fn.__name__ + str(args) + str(kwargs)
            value = await cache.get(key)
            if value:
                return value
            else:
                res = await fn(*args, **kwargs)
                await cache.set(key, res, ttl=ttl)
                return res
        return wrapper
    return cached_decorator


def get_default_cache(backend=None, serializer=None):
    backend = backend or RedisCache
    serializer = serializer() or None
    return backend(serializer=serializer)
