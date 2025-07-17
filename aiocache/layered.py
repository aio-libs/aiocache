"""
Layered cache implementation for aiocache.

This module provides a layered cache that can combine multiple cache backends
in a hierarchy, typically with faster caches (like memory) as L1 and slower
but more persistent caches (like Redis) as L2+.
"""

import asyncio
import importlib
import logging
from typing import Any, Dict, List, Optional, Type, Union

from .base import BaseCache
from .serializers import BaseSerializer

logger = logging.getLogger(__name__)


class LayeredCache(BaseCache[str]):
    """
    A cache that combines multiple cache backends in a layered hierarchy.
    
    The cache layers are ordered from fastest (L1) to slowest (L2, L3, etc.).
    When getting a value, it checks each layer in order until found.
    When setting a value, it writes to all layers.
    
    :param layers: List of cache instances ordered from fastest to slowest
    :param namespace: string to use as default prefix for the key
    :param timeout: int or float in seconds specifying maximum timeout
    :param ttl: int the expiration time in seconds to use as default
    """

    NAME = "layered"

    def __init__(self, layers: List[BaseCache], **kwargs):
        if not layers:
            raise ValueError("At least one cache layer must be provided")
        
        # Use the first layer's serializer and plugins as defaults
        first_layer = layers[0]
        if "serializer" not in kwargs:
            kwargs["serializer"] = first_layer.serializer
        if "plugins" not in kwargs:
            kwargs["plugins"] = first_layer.plugins
        if "namespace" not in kwargs:
            kwargs["namespace"] = first_layer.namespace
        if "timeout" not in kwargs:
            kwargs["timeout"] = first_layer.timeout
        if "ttl" not in kwargs:
            kwargs["ttl"] = first_layer.ttl
        if "key_builder" not in kwargs:
            kwargs["key_builder"] = first_layer._build_key
            
        super().__init__(**kwargs)
        self.layers = layers

    async def _get(self, key, encoding="utf-8", _conn=None):
        """Get value from cache layers, checking from fastest to slowest."""
        for i, layer in enumerate(self.layers):
            try:
                value = await layer.get(key, encoding=encoding, _conn=_conn)
                if value is not None:
                    await self._populate_faster_layers(key, value, i)
                    return value
            except Exception as e:
                logger.warning(f"Error getting from layer {i} ({layer.NAME}): {e}")
                continue
        return None

    async def _gets(self, key, encoding="utf-8", _conn=None):
        for i, layer in enumerate(self.layers):
            try:
                value = await layer.gets(key, encoding=encoding, _conn=_conn)
                if value is not None:
                    await self._populate_faster_layers(key, value, i)
                    return value
            except Exception as e:
                logger.warning(f"Error getting from layer {i} ({layer.NAME}): {e}")
                continue
        return None

    async def _multi_get(self, keys, encoding="utf-8", _conn=None):
        result = [None] * len(keys)
        missing_indices = list(range(len(keys)))
        for i, layer in enumerate(self.layers):
            if not missing_indices:
                break
            try:
                layer_keys = [keys[j] for j in missing_indices]
                layer_values = await layer.multi_get(layer_keys, encoding=encoding, _conn=_conn)
                new_missing = []
                for idx, (orig_idx, value) in enumerate(zip(missing_indices, layer_values)):
                    if value is not None:
                        result[orig_idx] = value
                        await self._populate_faster_layers(keys[orig_idx], value, i)
                    else:
                        new_missing.append(orig_idx)
                missing_indices = new_missing
            except Exception as e:
                logger.warning(f"Error multi_get from layer {i} ({layer.NAME}): {e}")
                continue
        return result

    async def _set(self, key, value, ttl=None, _cas_token=None, _conn=None):
        success = True
        for i, layer in enumerate(self.layers):
            try:
                await layer.set(key, value, ttl=ttl, _cas_token=_cas_token, _conn=_conn)
            except Exception as e:
                logger.warning(f"Error setting in layer {i} ({layer.NAME}): {e}")
                success = False
        return success

    async def _multi_set(self, pairs, ttl=None, _conn=None):
        success = True
        for i, layer in enumerate(self.layers):
            try:
                await layer.multi_set(pairs, ttl=ttl, _conn=_conn)
            except Exception as e:
                logger.warning(f"Error multi_set in layer {i} ({layer.NAME}): {e}")
                success = False
        return success

    async def _add(self, key, value, ttl=None, _conn=None):
        success = True
        for i, layer in enumerate(self.layers):
            try:
                result = await layer.add(key, value, ttl=ttl, _conn=_conn)
                if not result:
                    success = False
            except Exception as e:
                logger.warning(f"Error adding to layer {i} ({layer.NAME}): {e}")
                success = False
        return success

    async def _delete(self, key, _conn=None):
        deleted_count = 0
        for i, layer in enumerate(self.layers):
            try:
                count = await layer.delete(key, _conn=_conn)
                deleted_count = max(deleted_count, count)
            except Exception as e:
                logger.warning(f"Error deleting from layer {i} ({layer.NAME}): {e}")
        return deleted_count

    async def _multi_delete(self, keys, _conn=None):
        deleted_count = 0
        for i, layer in enumerate(self.layers):
            try:
                count = await layer.multi_delete(keys, _conn=_conn)
                deleted_count = max(deleted_count, count)
            except Exception as e:
                logger.warning(f"Error multi_delete from layer {i} ({layer.NAME}): {e}")
        return deleted_count

    async def _exists(self, key, _conn=None):
        for i, layer in enumerate(self.layers):
            try:
                if await layer.exists(key, _conn=_conn):
                    return True
            except Exception as e:
                logger.warning(f"Error checking exists in layer {i} ({layer.NAME}): {e}")
                continue
        return False

    async def _increment(self, key, delta=1, _conn=None):
        result = None
        for i, layer in enumerate(self.layers):
            try:
                value = await layer.increment(key, delta=delta, _conn=_conn)
                if result is None:
                    result = value
            except Exception as e:
                logger.warning(f"Error incrementing in layer {i} ({layer.NAME}): {e}")
        return result

    async def _expire(self, key, ttl, _conn=None):
        success = True
        for i, layer in enumerate(self.layers):
            try:
                await layer.expire(key, ttl, _conn=_conn)
            except Exception as e:
                logger.warning(f"Error setting expire in layer {i} ({layer.NAME}): {e}")
                success = False
        return success

    async def _clear(self, namespace=None, _conn=None):
        success = True
        for i, layer in enumerate(self.layers):
            try:
                await layer.clear(namespace=namespace, _conn=_conn)
            except Exception as e:
                logger.warning(f"Error clearing layer {i} ({layer.NAME}): {e}")
                success = False
        return success

    async def _raw(self, command, *args, _conn=None, **kwargs):
        if self.layers:
            # Only pass encoding if the first layer expects it
            import inspect
            sig = inspect.signature(self.layers[0]._raw)
            if 'encoding' in sig.parameters:
                return await self.layers[0]._raw(command, *args, encoding=self.serializer.encoding, _conn=_conn, **kwargs)
            else:
                return await self.layers[0]._raw(command, *args, _conn=_conn, **kwargs)
        return None

    async def _close(self, _conn=None):
        """Close all cache layers."""
        for i, layer in enumerate(self.layers):
            try:
                await layer.close(_conn=_conn)
            except Exception as e:
                logger.warning(f"Error closing layer {i} ({layer.NAME}): {e}")

    async def _redlock_release(self, key, value):
        """Release redlock - delegate to first layer."""
        if self.layers:
            return await self.layers[0]._redlock_release(key, value)
        return False

    def build_key(self, key: str, namespace=None):
        """Build key using the first layer's key builder."""
        if self.layers:
            return self.layers[0].build_key(key, namespace)
        return self._str_build_key(key, namespace)

    async def _populate_faster_layers(self, key: str, value: Any, found_layer_index: int):
        """Populate faster layers with a value found in a slower layer."""
        for i in range(found_layer_index):
            try:
                await self.layers[i].set(key, value)
            except Exception as e:
                logger.debug(f"Error populating layer {i} ({self.layers[i].NAME}): {e}")

    async def __aenter__(self):
        """Enter context manager for all layers."""
        for layer in self.layers:
            await layer.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager for all layers."""
        for layer in self.layers:
            await layer.__aexit__(exc_type, exc_val, exc_tb)


def create_cache_from_config(config: Dict[str, Any]) -> BaseCache:
    """
    Create a cache instance from configuration dictionary.
    
    :param config: Configuration dictionary with cache settings
    :return: Configured cache instance
    """
    cache_class_name = config["cache"]
    
    # Import the cache class
    module_name, class_name = cache_class_name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    cache_class = getattr(module, class_name)
    
    # Prepare constructor arguments
    kwargs = {}
    
    # Handle serializer configuration
    if "serializer" in config:
        serializer_config = config["serializer"]
        serializer_class_name = serializer_config["class"]
        serializer_module_name, serializer_class_name = serializer_class_name.rsplit(".", 1)
        serializer_module = importlib.import_module(serializer_module_name)
        serializer_class = getattr(serializer_module, serializer_class_name)
        kwargs["serializer"] = serializer_class()
    
    # Handle other configuration options
    for key, value in config.items():
        if key not in ["cache", "serializer"]:
            kwargs[key] = value
    
    # Create cache instance
    return cache_class(**kwargs)


def create_layered_cache(cache_configs: List[Dict[str, Any]], **kwargs) -> LayeredCache:
    """
    Create a layered cache from a list of cache configurations.
    
    :param cache_configs: List of cache configuration dictionaries
    :param kwargs: Additional arguments to pass to LayeredCache
    :return: Configured LayeredCache instance
    """
    layers = []
    for config in cache_configs:
        cache = create_cache_from_config(config)
        layers.append(cache)
    
    return LayeredCache(layers, **kwargs)


def create_cache_from_dict(config: Dict[str, Any]) -> BaseCache:
    """
    Create a cache from configuration dictionary that can be either a single cache
    or a layered cache configuration.
    
    :param config: Configuration dictionary
    :return: Configured cache instance
    """
    if "cache" in config:
        # Single cache configuration
        return create_cache_from_config(config)
    elif "layers" in config:
        # Layered cache configuration
        return create_layered_cache(config["layers"], **{k: v for k, v in config.items() if k != "layers"})
    else:
        raise ValueError("Configuration must contain either 'cache' or 'layers' key") 