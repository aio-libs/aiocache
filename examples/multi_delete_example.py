#!/usr/bin/env python3
"""
Example demonstrating the multi_delete functionality in aiocache.

This example shows how to delete multiple keys at once from the cache,
which is more efficient than deleting keys one by one.
"""

import asyncio

from aiocache import SimpleMemoryCache


async def main():
    # Create a simple memory cache
    cache = SimpleMemoryCache()

    # Set multiple values
    await cache.set("user:1", "Alice")
    await cache.set("user:2", "Bob")
    await cache.set("user:3", "Charlie")
    await cache.set("user:4", "David")

    print("Initial cache state:")
    print(f"user:1 = {await cache.get('user:1')}")
    print(f"user:2 = {await cache.get('user:2')}")
    print(f"user:3 = {await cache.get('user:3')}")
    print(f"user:4 = {await cache.get('user:4')}")

    # Delete multiple keys at once
    deleted_count = await cache.multi_delete(["user:1", "user:3", "user:5"])
    print(f"\nDeleted {deleted_count} keys using multi_delete")

    print("\nCache state after multi_delete:")
    print(f"user:1 = {await cache.get('user:1')}")
    print(f"user:2 = {await cache.get('user:2')}")
    print(f"user:3 = {await cache.get('user:3')}")
    print(f"user:4 = {await cache.get('user:4')}")

    # Delete remaining keys
    deleted_count = await cache.multi_delete(["user:2", "user:4"])
    print(f"\nDeleted {deleted_count} remaining keys")

    print("\nFinal cache state:")
    print(f"user:1 = {await cache.get('user:1')}")
    print(f"user:2 = {await cache.get('user:2')}")
    print(f"user:3 = {await cache.get('user:3')}")
    print(f"user:4 = {await cache.get('user:4')}")

    # Test with empty list
    deleted_count = await cache.multi_delete([])
    print(f"\nDeleted {deleted_count} keys from empty list")


if __name__ == "__main__":
    asyncio.run(main()) 