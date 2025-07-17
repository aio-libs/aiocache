#!/usr/bin/env python3
"""
Example demonstrating the layered cache functionality in aiocache.

This example shows how to create a multi-layer cache with memory as L1
and Redis as L2, providing both speed and persistence.
"""

import asyncio
from collections import namedtuple

from aiocache import create_cache_from_dict, create_layered_cache
from aiocache.backends.memory import SimpleMemoryCache
from aiocache.serializers import StringSerializer, PickleSerializer

# Example 1: Using the configuration dictionary format
async def example_with_config_dict():
    """Example using the configuration dictionary format."""
    
    config = {
        'layers': [
            {
                'cache': "aiocache.SimpleMemoryCache",
                'serializer': {
                    'class': "aiocache.serializers.StringSerializer"
                }
            },
            {
                'cache': "aiocache.RedisCache",
                'endpoint': "127.0.0.1",
                'port': 6379,
                'timeout': 1,
                'serializer': {
                    'class': "aiocache.serializers.PickleSerializer"
                }
            }
        ]
    }
    
    # Create layered cache from configuration
    cache = create_cache_from_dict(config)
    
    async with cache:
        # Set a value - it will be stored in both layers
        await cache.set("user:1", "Alice")
        await cache.set("user:2", "Bob")
        
        # Get values - they will be retrieved from L1 (memory) if available
        print(f"user:1 = {await cache.get('user:1')}")
        print(f"user:2 = {await cache.get('user:2')}")
        
        # Clear L1 cache to simulate cache miss
        await cache.layers[0].clear()
        
        # Get again - this time it will be retrieved from L2 (Redis) and populate L1
        print(f"After L1 clear, user:1 = {await cache.get('user:1')}")
        print(f"After L1 clear, user:2 = {await cache.get('user:2')}")


# Example 2: Using the programmatic approach
async def example_programmatic():
    """Example using the programmatic approach."""
    
    # Create individual cache layers
    memory_cache = SimpleMemoryCache(
        serializer=StringSerializer(),
        namespace="l1"
    )
    
    # For this example, we'll use memory as both layers since Redis requires setup
    # In a real scenario, you'd use RedisCache here
    redis_cache = SimpleMemoryCache(
        serializer=PickleSerializer(),
        namespace="l2"
    )
    
    # Create layered cache
    cache = create_layered_cache([memory_cache, redis_cache])
    
    async with cache:
        # Set complex data
        user_data = {
            "name": "Charlie",
            "age": 30,
            "email": "charlie@example.com"
        }
        
        await cache.set("user:3", user_data)
        
        # Get the data
        retrieved_data = await cache.get("user:3")
        print(f"Retrieved user data: {retrieved_data}")
        
        # Test multi operations
        await cache.multi_set([
            ("key1", "value1"),
            ("key2", "value2"),
            ("key3", "value3")
        ])
        
        values = await cache.multi_get(["key1", "key2", "key3"])
        print(f"Multi-get results: {values}")
        
        # Test multi delete
        deleted_count = await cache.multi_delete(["key1", "key2"])
        print(f"Deleted {deleted_count} keys")


# Example 3: Performance comparison
async def performance_comparison():
    """Compare performance between single and layered caches."""
    
    # Single memory cache
    single_cache = SimpleMemoryCache()
    
    # Layered cache (memory + memory for demo)
    layered_cache = create_layered_cache([
        SimpleMemoryCache(namespace="l1"),
        SimpleMemoryCache(namespace="l2")
    ])
    
    async with single_cache, layered_cache:
        # Test single cache performance
        start_time = asyncio.get_event_loop().time()
        
        for i in range(100):
            await single_cache.set(f"key{i}", f"value{i}")
            await single_cache.get(f"key{i}")
        
        single_time = asyncio.get_event_loop().time() - start_time
        
        # Test layered cache performance
        start_time = asyncio.get_event_loop().time()
        
        for i in range(100):
            await layered_cache.set(f"key{i}", f"value{i}")
            await layered_cache.get(f"key{i}")
        
        layered_time = asyncio.get_event_loop().time() - start_time
        
        print(f"Single cache time: {single_time:.4f}s")
        print(f"Layered cache time: {layered_time:.4f}s")
        print(f"Overhead: {((layered_time - single_time) / single_time * 100):.2f}%")


async def main():
    """Run all examples."""
    print("=== Layered Cache Example ===\n")
    
    print("1. Configuration Dictionary Example:")
    try:
        await example_with_config_dict()
    except Exception as e:
        print(f"   Skipped (Redis not available): {e}")
    
    print("\n2. Programmatic Example:")
    await example_programmatic()
    
    print("\n3. Performance Comparison:")
    await performance_comparison()


if __name__ == "__main__":
    asyncio.run(main()) 