#!/usr/bin/env python3
"""
Real-world example: Web application with LayeredCache

This example demonstrates how LayeredCache can be used in a typical web application
scenario where you want fast access to frequently accessed data while maintaining
persistence for less frequently accessed data.

Scenario: A web application that serves user profiles and product information
with different caching strategies based on access patterns.
"""

import asyncio
import time
from typing import Dict, Any, Optional

from aiocache import LayeredCache, SimpleMemoryCache, RedisCache
from aiocache.serializers import JsonSerializer


class UserProfileService:
    """Service for managing user profile data with layered caching."""
    
    def __init__(self):
        # Create a layered cache with memory L1 and Redis L2
        # Memory cache for ultra-fast access to hot data
        memory_cache = SimpleMemoryCache(
            serializer=JsonSerializer(),
            ttl=300,  # 5 minutes for memory cache
            maxsize=1000  # Limit memory usage
        )
        
        # Redis cache for persistent storage of warm data
        redis_cache = RedisCache(
            serializer=JsonSerializer(),
            ttl=3600,  # 1 hour for Redis cache
            endpoint="127.0.0.1",
            port=6379,
            db=0
        )
        
        self.cache = LayeredCache([memory_cache, redis_cache])
        
        # Simulate database storage
        self.db = {}
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile with layered caching."""
        cache_key = f"user_profile:{user_id}"
        
        # Try to get from cache first
        profile = await self.cache.get(cache_key)
        if profile:
            print(f"✅ Cache HIT for user {user_id}")
            return profile
        
        # Cache miss - fetch from database
        print(f"❌ Cache MISS for user {user_id} - fetching from database")
        profile = await self._fetch_from_database(user_id)
        
        if profile:
            # Store in cache for future requests
            await self.cache.set(cache_key, profile)
            print(f"💾 Stored user {user_id} in cache")
        
        return profile
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile and invalidate cache."""
        # Update database
        success = await self._update_database(user_id, profile_data)
        
        if success:
            # Invalidate cache entry
            cache_key = f"user_profile:{user_id}"
            await self.cache.delete(cache_key)
            print(f"🗑️ Invalidated cache for user {user_id}")
        
        return success
    
    async def get_multiple_profiles(self, user_ids: list) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple user profiles efficiently using multi_get."""
        cache_keys = [f"user_profile:{user_id}" for user_id in user_ids]
        
        # Try to get all from cache
        cached_profiles = await self.cache.multi_get(cache_keys)
        
        # Process results
        results = {}
        missing_user_ids = []
        
        for user_id, profile in zip(user_ids, cached_profiles):
            if profile:
                results[user_id] = profile
                print(f"✅ Cache HIT for user {user_id}")
            else:
                missing_user_ids.append(user_id)
                print(f"❌ Cache MISS for user {user_id}")
        
        # Fetch missing profiles from database
        if missing_user_ids:
            print(f"📊 Fetching {len(missing_user_ids)} profiles from database")
            for user_id in missing_user_ids:
                profile = await self._fetch_from_database(user_id)
                if profile:
                    cache_key = f"user_profile:{user_id}"
                    await self.cache.set(cache_key, profile)
                    results[user_id] = profile
                    print(f"💾 Stored user {user_id} in cache")
        
        return results
    
    async def _fetch_from_database(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Simulate database fetch with delay."""
        await asyncio.sleep(0.1)  # Simulate database latency
        
        # Simulate database lookup
        if user_id in self.db:
            return self.db[user_id]
        
        # Simulate creating a new profile
        profile = {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "created_at": time.time(),
            "last_login": time.time()
        }
        self.db[user_id] = profile
        return profile
    
    async def _update_database(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Simulate database update."""
        await asyncio.sleep(0.05)  # Simulate database write latency
        self.db[user_id] = {**self.db.get(user_id, {}), **profile_data}
        return True


class ProductCatalogService:
    """Service for managing product catalog with different caching strategy."""
    
    def __init__(self):
        # For product catalog, we use longer TTL since data changes less frequently
        memory_cache = SimpleMemoryCache(
            serializer=JsonSerializer(),
            ttl=1800,  # 30 minutes for memory cache
            maxsize=500
        )
        
        redis_cache = RedisCache(
            serializer=JsonSerializer(),
            ttl=7200,  # 2 hours for Redis cache
            endpoint="127.0.0.1",
            port=6379,
            db=1  # Different database for products
        )
        
        self.cache = LayeredCache([memory_cache, redis_cache])
        self.db = {}
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product information with layered caching."""
        cache_key = f"product:{product_id}"
        
        product = await self.cache.get(cache_key)
        if product:
            print(f"✅ Cache HIT for product {product_id}")
            return product
        
        print(f"❌ Cache MISS for product {product_id} - fetching from database")
        product = await self._fetch_product_from_database(product_id)
        
        if product:
            await self.cache.set(cache_key, product)
            print(f"💾 Stored product {product_id} in cache")
        
        return product
    
    async def _fetch_product_from_database(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Simulate product database fetch."""
        await asyncio.sleep(0.2)  # Simulate slower product database
        
        if product_id in self.db:
            return self.db[product_id]
        
        # Simulate creating a new product
        product = {
            "id": product_id,
            "name": f"Product {product_id}",
            "price": 99.99,
            "category": "electronics",
            "in_stock": True,
            "description": f"Description for product {product_id}"
        }
        self.db[product_id] = product
        return product


async def simulate_web_requests():
    """Simulate realistic web application traffic patterns."""
    print("🚀 Starting real-world LayeredCache example...\n")
    
    # Initialize services
    user_service = UserProfileService()
    product_service = ProductCatalogService()
    
    # Simulate user profile requests
    print("👥 Simulating user profile requests:")
    print("=" * 50)
    
    # First request - cache miss, then subsequent hits
    print("\n1. First request for user 'alice' (cache miss):")
    start_time = time.time()
    profile = await user_service.get_user_profile("alice")
    print(f"⏱️ Time taken: {time.time() - start_time:.3f}s")
    
    print("\n2. Second request for user 'alice' (cache hit from memory):")
    start_time = time.time()
    profile = await user_service.get_user_profile("alice")
    print(f"⏱️ Time taken: {time.time() - start_time:.3f}s")
    
    # Multiple users
    print("\n3. Multiple user requests:")
    start_time = time.time()
    profiles = await user_service.get_multiple_profiles(["bob", "charlie", "diana"])
    print(f"⏱️ Time taken: {time.time() - start_time:.3f}s")
    
    # Update profile and invalidate cache
    print("\n4. Update user profile and invalidate cache:")
    await user_service.update_user_profile("alice", {"last_login": time.time()})
    
    print("\n5. Request updated profile (cache miss due to invalidation):")
    start_time = time.time()
    profile = await user_service.get_user_profile("alice")
    print(f"⏱️ Time taken: {time.time() - start_time:.3f}s")
    
    # Simulate product catalog requests
    print("\n🛍️ Simulating product catalog requests:")
    print("=" * 50)
    
    print("\n1. First request for product 'laptop-001' (cache miss):")
    start_time = time.time()
    product = await product_service.get_product("laptop-001")
    print(f"⏱️ Time taken: {time.time() - start_time:.3f}s")
    
    print("\n2. Second request for product 'laptop-001' (cache hit):")
    start_time = time.time()
    product = await product_service.get_product("laptop-001")
    print(f"⏱️ Time taken: {time.time() - start_time:.3f}s")
    
    # Simulate cache layer behavior
    print("\n🔍 Demonstrating cache layer behavior:")
    print("=" * 50)
    
    print("\n1. Request for new user 'eve' (will populate both layers):")
    await user_service.get_user_profile("eve")
    
    print("\n2. Request for new product 'phone-001' (will populate both layers):")
    await product_service.get_product("phone-001")
    
    print("\n✅ Real-world example completed!")
    print("\nKey benefits demonstrated:")
    print("• Fast access to frequently accessed data (memory cache)")
    print("• Persistent storage for less frequent data (Redis cache)")
    print("• Automatic population of faster layers from slower layers")
    print("• Efficient bulk operations with multi_get")
    print("• Cache invalidation for data updates")


async def main():
    """Main function to run the example."""
    try:
        await simulate_web_requests()
    except Exception as e:
        print(f"❌ Error running example: {e}")
        print("Note: This example requires Redis to be running on localhost:6379")
        print("To run without Redis, modify the example to use only memory cache")


if __name__ == "__main__":
    asyncio.run(main()) 