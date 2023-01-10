"""alt_key_builder.py

    ``key_builder`` is used in two contexts within ``aiocache``,
    with different meanings.
    1. Custom ``key_builder`` for a cache -- Prepends a namespace to the key
    2. Custom ``key_builder`` for a cache decorator -- Creates a cache key from
       the decorated callable and the callable's arguments

    --------------------------------------------------------------------------
    1. A custom ``key_builder`` for a cache can manipulate the name of a
       cache key; for example to meet naming requirements of the backend.

    ``key_builder`` can also optionally mark the key as belonging to a
    namespace group. This enables commonly used key names to be disambiguated
    by their ``namespace`` value. It also enables bulk operation on cache keys,
    such as expiring all keys in the same namespace.

    ``key_builder`` is expected (but not required) to prefix the passed key
    argument with the namespace argument. After initializing the cache object,
    the key builder can be accessed via the cache's ``build_key`` member.

    Args:
        key (str): undecorated key name
        namespace (str, optional): Prefix to add to the key. Defaults to None.

    Returns:
        By default, ``cache.build_key()`` returns ``f'{namespace}{sep}{key}'``,
        where some backends might include an optional separator, ``sep``.
        Some backends might strip or replace illegal characters, and encode
        the result before returning it. Typically str or bytes.

    --------------------------------------------------------------------------
    2. Custom ``key_builder`` for a cache decorator automatically generates a
       cache key from the call signature of the decorated callable. It does
       not accept a ``namespace`` parameter, and it should not add a
       naemspace to the key that it outputs.

    Args:
        func (callable): name of the decorated callable
        *args: Positional arguments when ``func`` was called.
        **kwargs: Keyword arguments when ``func`` was called.

    Returns (str):
        By default, the output key is a concatenation of the module and name
        of ``func`` + the positional arguments + the sorted keyword arguments.
"""
import asyncio
from typing import List, Dict

from aiocache import Cache, cached


async def demo_key_builders():
    await demo_cache_key_builders()
    await demo_cache_key_builders(namespace="demo")
    await demo_decorator_key_builders()


# 1. Custom ``key_builder`` for a cache
# -------------------------------------

def ensure_no_spaces(key, namespace=None, replace='_'):
    """Prefix key with namespace; replace each space with ``replace``"""
    aggregate_key = f"{namespace or ''}{key}"
    custom_key = aggregate_key.replace(' ', replace)
    return custom_key


def bytes_key(key, namespace=None):
    """Prefix key with namespace; convert output to bytes"""
    aggregate_key = f"{namespace or ''}{key}"
    custom_key = aggregate_key.encode()
    return custom_key


def fixed_key(key, namespace=None):
    """Ignore input, generate a fixed key"""
    unchanging_key = "universal key"
    return unchanging_key


async def demo_cache_key_builders(namespace=None):
    """Demonstrate usage and behavior of the custom key_builder functions"""
    cache_ns = "cache_namespace"
    async with Cache(Cache.MEMORY, key_builder=ensure_no_spaces, namespace=cache_ns) as cache:
        raw_key = "Key With Unwanted Spaces"
        return_value = 42
        await cache.add(raw_key, return_value, namespace=namespace)
        exists = await cache.exists(raw_key, namespace=namespace)
        assert exists is True
        custom_key = cache.build_key(raw_key, namespace=namespace)
        assert ' ' not in custom_key
        if namespace is not None:
            assert custom_key.startswith(namespace)
        else:
            # Using cache.namespace instead
            exists = await cache.exists(raw_key, namespace=cache_ns)
            assert exists is True
            custom_key = cache.build_key(raw_key, namespace=cache_ns)
            assert custom_key.startswith(cache_ns)
        cached_value = await cache.get(raw_key, namespace=namespace)
        assert cached_value == return_value
        await cache.delete(raw_key, namespace=namespace)

    async with Cache(Cache.MEMORY, key_builder=bytes_key) as cache:
        raw_key = "string-key"
        return_value = 42
        await cache.add(raw_key, return_value, namespace=namespace)
        exists = await cache.exists(raw_key, namespace=namespace)
        assert exists is True
        custom_key = cache.build_key(raw_key, namespace=namespace)
        assert isinstance(custom_key, bytes)
        cached_value = await cache.get(raw_key, namespace=namespace)
        assert cached_value == return_value
        await cache.delete(raw_key, namespace=namespace)

    async with Cache(Cache.MEMORY, key_builder=fixed_key) as cache:
        unchanging_key = "universal key"

        for raw_key, return_value in zip(
                ("key_1", "key_2", "key_3"),
                ("val_1", "val_2", "val_3")):
            await cache.set(raw_key, return_value, namespace=namespace)
            exists = await cache.exists(raw_key, namespace=namespace)
            assert exists is True
            custom_key = cache.build_key(raw_key, namespace=namespace)
            assert custom_key == unchanging_key
            cached_value = await cache.get(raw_key, namespace=namespace)
            assert cached_value == return_value

        # Cache key exists regardless of raw_key name
        for raw_key in ("key_1", "key_2", "key_3"):
            exists = await cache.exists(raw_key, namespace=namespace)
            assert exists is True

        cached_value = await cache.get(raw_key, namespace=namespace)
        assert cached_value == "val_3"  # The last value that was set
        await cache.delete(raw_key, namespace=namespace)

        # Deleting one cache key deletes them all
        for raw_key in ("key_1", "key_2", "key_3"):
            exists = await cache.exists(raw_key, namespace=namespace)
            assert exists is False


# 2. Custom ``key_builder`` for a cache decorator
# -----------------------------------------------

def ignore_kwargs(func, *args, **kwargs):
    """Do not use keyword arguments in the cache key's name"""
    return (
        (func.__module__ or "")
        + func.__name__
        + str(args)
    )


def module_override(func, *args, **kwargs):
    """Override the module-name prefix for the cache key"""
    ordered_kwargs = sorted(kwargs.items())
    return (
        "my_module_alias"
        + func.__name__
        + str(args)
        + str(ordered_kwargs)
    )


def hashed_args(*args, **kwargs):
    """Return a hashable key from a callable's parameters"""
    key = tuple()
    for arg in args:
        if isinstance(arg, List):
            key += tuple(hashed_args(_arg) for _arg in arg)
        elif isinstance(arg, Dict):
            key += tuple(sorted(
                (_key, hashed_args(_value)) for (_key, _value) in arg.items()
            ))
        else:
            key += (arg, )
    key += tuple(sorted(
        (_key, hashed_args(_value)) for (_key, _value) in kwargs.items()
    ))
    return key


def structured_key(func, *args, **kwargs):
    """String representation of a structured call signature"""
    key = tuple()
    key += (func.__module__ or '', )
    key += (func.__qualname__ or func.__name__, )
    key += hashed_args(*args, **kwargs)
    return str(key)


async def demo_decorator_key_builders():
    """Demonstrate usage and behavior of the custom key_builder functions"""
    await demo_ignore_kwargs_decorator()
    await demo_module_override_decorator()
    await demo_structured_key_decorator()


async def demo_ignore_kwargs_decorator():
    """Cache key from positional arguments in call to decorated function"""
    @cached(key_builder=ignore_kwargs)
    async def fn(a, b=2, c=3):
        return (a, b)

    (a, b) = (5, 1)
    demo_params = (
        dict(args=(a, b), kwargs=dict(c=3), ret=(a, b)),
        dict(args=(a, ), kwargs=dict(b=b, c=3), ret=(a, b)),
        dict(args=(a, ), kwargs=dict(c=3), ret=(a, b)),  # b from previous call
        dict(args=(a, b, 6), kwargs={}, ret=(a, b)),
    )
    demo_keys = list()

    for params in demo_params:
        args = params["args"]
        kwargs = params["kwargs"]

        await fn(*args, **kwargs)
        cache = fn.cache
        decorator = cached(key_builder=ignore_kwargs)
        key = decorator.get_cache_key(fn, args=args, kwargs=kwargs)
        exists = await cache.exists(key)
        assert exists is True
        assert key.endswith(str(args))
        cached_value = await cache.get(key)
        assert cached_value == params["ret"]
        demo_keys.append(key)

    assert demo_keys[1] == demo_keys[2]
    assert demo_keys[0] != demo_keys[1]
    assert demo_keys[0] != demo_keys[3]
    assert demo_keys[1] != demo_keys[3]

    for key in set(demo_keys):
        await cache.delete(key)


async def demo_module_override_decorator():
    """Cache key uses custom module name for decorated function"""
    @cached(key_builder=module_override)
    async def fn(a, b=2, c=3):
        return (a, b)

    (a, b) = (5, 1)
    args = (a, b)
    kwargs = dict(c=3)
    return_value = (a, b)

    await fn(*args, **kwargs)
    cache = fn.cache
    decorator = cached(key_builder=module_override)
    key = decorator.get_cache_key(fn, args=args, kwargs=kwargs)
    exists = await cache.exists(key)
    assert exists is True
    assert key.startswith("my_module_alias")
    cached_value = await cache.get(key)
    assert cached_value == return_value
    await cache.delete(key)


async def demo_structured_key_decorator():
    """Cache key expresses structure of decorated function call"""
    @cached(key_builder=structured_key)
    async def fn(a, b=2, c=3):
        return (a, b)

    (a, b) = (5, 1)
    args = (a, b)
    kwargs = dict(c=3)
    return_value = (a, b)
    fn_module = fn.__module__ or ''
    fn_name = fn.__qualname__ or fn.__name__
    key_name = str((fn_module, fn_name) + hashed_args(*args, **kwargs))

    await fn(*args, **kwargs)
    cache = fn.cache
    decorator = cached(key_builder=structured_key)
    key = decorator.get_cache_key(fn, args=args, kwargs=kwargs)
    exists = await cache.exists(key)
    assert exists is True
    assert key == key_name
    cached_value = await cache.get(key)
    assert cached_value == return_value
    await cache.delete(key)

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(demo_key_builders())
