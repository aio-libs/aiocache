#!/usr/bin/env python3
"""
Simple LayeredCache example using only memory caches

This example demonstrates LayeredCache functionality without requiring Redis
or other external dependencies. It uses two memory caches with different TTLs
to simulate a fast L1 cache and a slower L2 cache.
"""

import asyncio
import time
from typing import Dict, Any, Optional

from aiocache import LayeredCache, SimpleMemoryCache
from aiocache.serializers import JsonSerializer


class SimpleLayeredCacheExample:
    """Simple example using LayeredCache with memory caches only."""
    
    def __init__(self):
        # Create two memory caches with different TTLs to simulate L1 and L2
        # L1: Fast cache with short TTL (5 seconds)
        l1_cache = SimpleMemoryCache(
            serializer=JsonSerializer(),
            ttl=5,  # 5 seconds
            maxsize=100
        )
        
        # L2: Slower cache with longer TTL (30 seconds)
        l2_cache = SimpleMemoryCache(
            serializer=JsonSerializer(),
            ttl=30,  # 30 seconds
            maxsize=1000
        )
        
        # Create layered cache
        self.cache = LayeredCache([l1_cache, l2_cache])
        
        # Simulate database
        self.db = {}
    
    async def get_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data with layered caching."""
        # Try to get from cache first
        data = await self.cache.get(key)
        if data:
            print(f"✅ Cache HIT for '{key}'")
            return data
        
        # Cache miss - fetch from database
        print(f"❌ Cache MISS for '{key}' - fetching from database")
        data = await self._fetch_from_database(key)
        
        if data:
            # Store in cache for future requests
            await self.cache.set(key, data)
            print(f"💾 Stored '{key}' in cache")
        
        return data
    
    async def get_multiple_data(self, keys: list) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple data items efficiently using multi_get."""
        # Try to get all from cache
        cached_data = await self.cache.multi_get(keys)
        
        # Process results
        results = {}
        missing_keys = []
        
        for key, data in zip(keys, cached_data):
            if data:
                results[key] = data
                print(f"✅ Cache HIT for '{key}'")
            else:
                missing_keys.append(key)
                print(f"❌ Cache MISS for '{key}'")
        
        # Fetch missing data from database
        if missing_keys:
            print(f"📊 Fetching {len(missing_keys)} items from database")
            for key in missing_keys:
                data = await self._fetch_from_database(key)
                if data:
                    await self.cache.set(key, data)
                    results[key] = data
                    print(f"💾 Stored '{key}' in cache")
        
        return results
    
    async def update_data(self, key: str, data: Dict[str, Any]) -> bool:
        """Update data and invalidate cache."""
        # Update database
        success = await self._update_database(key, data)
        
        if success:
            # Invalidate cache entry
            await self.cache.delete(key)
            print(f"🗑️ Invalidated cache for '{key}'")
        
        return success
    
    async def _fetch_from_database(self, key: str) -> Optional[Dict[str, Any]]:
        """Simulate database fetch with delay."""
        await asyncio.sleep(0.1)  # Simulate database latency
        
        # Simulate database lookup
        if key in self.db:
            return self.db[key]
        
        # Simulate creating new data
        data = {
            "key": key,
            "value": f"Data for {key}",
            "timestamp": time.time(),
            "source": "database"
        }
        self.db[key] = data
        return data
    
    async def _update_database(self, key: str, data: Dict[str, Any]) -> bool:
        """Simulate database update."""
        await asyncio.sleep(0.05)  # Simulate database write latency
        self.db[key] = {**self.db.get(key, {}), **data}
        return True


async def demonstrate_layered_cache():
    """Demonstrate LayeredCache functionality."""
    print("🚀 Simple LayeredCache Example")
    print("=" * 50)
    
    cache_example = SimpleLayeredCacheExample()
    
    # Test 1: First request (cache miss)
    print("\n1. First request for 'user:123' (cache miss):")
    start_time = time.time()
    data = await cache_example.get_data("user:123")
    print(f"⏱️ Time taken: {time.time() - start_time:.3f}s")
    print(f"📄 Data: {data}")
    
    # Test 2: Second request (cache hit from L1)
    print("\n2. Second request for 'user:123' (cache hit from L1):")
    start_time = time.time()
    data = await cache_example.get_data("user:123")
    print(f"⏱️ Time taken: {time.time() - start_time:.3f}s")
    print(f"📄 Data: {data}")
    
    # Test 3: Multiple requests
    print("\n3. Multiple requests:")
    start_time = time.time()
    results = await cache_example.get_multiple_data(["user:456", "user:789", "user:123"])
    print(f"⏱️ Time taken: {time.time() - start_time:.3f}s")
    print(f"📄 Results: {len(results)} items retrieved")
    
    # Test 4: Update data
    print("\n4. Update data and invalidate cache:")
    await cache_example.update_data("user:123", {"updated": True, "update_time": time.time()})
    
    # Test 5: Request updated data (cache miss due to invalidation)
    print("\n5. Request updated data (cache miss due to invalidation):")
    start_time = time.time()
    data = await cache_example.get_data("user:123")
    print(f"⏱️ Time taken: {time.time() - start_time:.3f}s")
    print(f"📄 Updated data: {data}")
    
    # Test 6: Demonstrate cache layer behavior
    print("\n6. Demonstrate cache layer behavior:")
    print("   - Adding new data that will populate both layers")
    await cache_example.get_data("product:abc")
    
    # Test 7: Wait for L1 cache to expire
    print("\n7. Waiting for L1 cache to expire (5 seconds)...")
    await asyncio.sleep(6)
    
    print("\n8. Request after L1 expiration (should hit L2):")
    start_time = time.time()
    data = await cache_example.get_data("user:123")
    print(f"⏱️ Time taken: {time.time() - start_time:.3f}s")
    print(f"📄 Data: {data}")
    
    print("\n✅ Simple LayeredCache example completed!")
    print("\nKey benefits demonstrated:")
    print("• Fast access to frequently accessed data (L1 cache)")
    print("• Persistent storage for less frequent data (L2 cache)")
    print("• Automatic population of faster layers from slower layers")
    print("• Efficient bulk operations with multi_get")
    print("• Cache invalidation for data updates")
    print("• Different TTL strategies for different cache layers")


async def main():
    """Main function to run the example."""
    try:
        await demonstrate_layered_cache()
    except Exception as e:
        print(f"❌ Error running example: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 