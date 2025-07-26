import pytest

from aiocache import create_layered_cache, create_cache_from_dict
from aiocache.backends.memory import SimpleMemoryCache
from aiocache.serializers import StringSerializer, NullSerializer, JsonSerializer


class TestLayeredCacheAcceptance:
    """Acceptance tests for LayeredCache with real backends."""

    @pytest.fixture
    def memory_l1(self):
        """Create L1 memory cache."""
        return SimpleMemoryCache(
            serializer=StringSerializer(),
            namespace="l1"
        )

    @pytest.fixture
    def memory_l2(self):
        """Create L2 memory cache."""
        return SimpleMemoryCache(
            serializer=JsonSerializer(),
            namespace="l2"
        )

    @pytest.fixture
    def layered_cache(self, memory_l1, memory_l2):
        """Create layered cache with two memory layers."""
        return create_layered_cache([memory_l1, memory_l2])

    async def test_basic_get_set(self, layered_cache):
        """Test basic get/set operations."""
        async with layered_cache:
            # Set value
            await layered_cache.set("key1", "value1")
            
            # Get value
            result = await layered_cache.get("key1")
            assert result == "value1"
            
            # Check that value exists in both layers
            assert await layered_cache.layers[0].get("key1") == "value1"
            assert await layered_cache.layers[1].get("key1") == "value1"

    async def test_cache_hierarchy(self, layered_cache):
        """Test that cache hierarchy works correctly."""
        async with layered_cache:
            # Set value in L2 only
            await layered_cache.layers[1].set("key1", "value1")
            
            # Clear L1 to simulate cache miss
            await layered_cache.layers[0].clear()
            
            # Get value - should be retrieved from L2 and populate L1
            result = await layered_cache.get("key1")
            assert result == "value1"
            
            # Now L1 should have the value
            assert await layered_cache.layers[0].get("key1") == "value1"

    async def test_multi_operations(self, layered_cache):
        """Test multi_get and multi_set operations."""
        async with layered_cache:
            # Multi set
            pairs = [("key1", "value1"), ("key2", "value2"), ("key3", "value3")]
            await layered_cache.multi_set(pairs)
            
            # Multi get
            values = await layered_cache.multi_get(["key1", "key2", "key3"])
            assert values == ["value1", "value2", "value3"]
            
            # Check both layers have the values
            l1_values = await layered_cache.layers[0].multi_get(["key1", "key2", "key3"])
            l2_values = await layered_cache.layers[1].multi_get(["key1", "key2", "key3"])
            assert l1_values == ["value1", "value2", "value3"]
            assert l2_values == ["value1", "value2", "value3"]

    async def test_multi_delete(self, layered_cache):
        """Test multi_delete operation."""
        async with layered_cache:
            # Set values
            await layered_cache.multi_set([
                ("key1", "value1"),
                ("key2", "value2"),
                ("key3", "value3")
            ])
            
            # Delete some keys
            deleted_count = await layered_cache.multi_delete(["key1", "key2"])
            assert deleted_count == 2
            
            # Check that keys are deleted from both layers
            assert await layered_cache.get("key1") is None
            assert await layered_cache.get("key2") is None
            assert await layered_cache.get("key3") == "value3"

    async def test_exists(self, layered_cache):
        """Test exists operation."""
        async with layered_cache:
            # Set value in L2 only
            await layered_cache.layers[1].set("key1", "value1")
            
            # Should exist
            assert await layered_cache.exists("key1") is True
            
            # Should not exist
            assert await layered_cache.exists("key2") is False

    async def test_increment(self, layered_cache):
        """Test increment operation."""
        async with layered_cache:
            # Increment non-existent key
            result = await layered_cache.increment("counter", delta=5)
            assert result == 5
            
            # Check both layers have the value
            assert await layered_cache.layers[0].get("counter") == 5
            assert await layered_cache.layers[1].get("counter") == 5
            
            # Increment again
            result = await layered_cache.increment("counter", delta=3)
            assert result == 8

    async def test_clear(self, layered_cache):
        """Test clear operation."""
        async with layered_cache:
            # Set values
            await layered_cache.set("key1", "value1")
            await layered_cache.set("key2", "value2")
            
            # Clear all
            await layered_cache.clear()
            
            # Check both layers are cleared
            assert await layered_cache.get("key1") is None
            assert await layered_cache.get("key2") is None

    async def test_ttl(self, layered_cache):
        """Test TTL functionality."""
        async with layered_cache:
            # Set with TTL
            await layered_cache.set("key1", "value1", ttl=1)
            
            # Should exist immediately
            assert await layered_cache.get("key1") == "value1"
            
            # Wait for expiration
            import asyncio
            await asyncio.sleep(1.1)
            
            # Should not exist anymore
            assert await layered_cache.get("key1") is None

    async def test_different_serializers(self, layered_cache):
        """Test that different serializers work correctly."""
        async with layered_cache:
            # Set complex data
            data = {"name": "Alice", "age": 30}
            await layered_cache.set("user", data)
            
            # Get data
            result = await layered_cache.get("user")
            assert result == data
            
            # Check that data is serialized correctly in both layers
            l1_data = await layered_cache.layers[0].get("user")
            l2_data = await layered_cache.layers[1].get("user")
            assert l1_data == data
            assert l2_data == data


class TestLayeredCacheFactory:
    """Test the layered cache factory functions."""

    def test_create_layered_cache_from_config(self):
        """Test creating layered cache from configuration."""
        config = {
            "layers": [
                {
                    "cache": "aiocache.SimpleMemoryCache",
                    "serializer": {
                        "class": "aiocache.serializers.StringSerializer"
                    },
                    "namespace": "l1"
                },
                {
                    "cache": "aiocache.SimpleMemoryCache",
                    "serializer": {
                        "class": "aiocache.serializers.JsonSerializer"
                    },
                    "namespace": "l2"
                }
            ],
            "namespace": "test"
        }
        
        cache = create_cache_from_dict(config)
        
        assert cache.NAME == "layered"
        assert len(cache.layers) == 2
        assert cache.namespace == "test"
        assert cache.layers[0].namespace == "l1"
        assert cache.layers[1].namespace == "l2"

    async def test_layered_cache_with_config(self):
        """Test that layered cache created from config works correctly."""
        config = {
            "layers": [
                {
                    "cache": "aiocache.SimpleMemoryCache",
                    "serializer": {
                        "class": "aiocache.serializers.StringSerializer"
                    }
                },
                {
                    "cache": "aiocache.SimpleMemoryCache",
                    "serializer": {
                        "class": "aiocache.serializers.JsonSerializer"
                    }
                }
            ]
        }
        
        cache = create_cache_from_dict(config)
        
        async with cache:
            # Test basic functionality
            await cache.set("key1", "value1")
            result = await cache.get("key1")
            assert result == "value1"
            
            # Test that both layers have the value
            assert await cache.layers[0].get("key1") == "value1"
            assert await cache.layers[1].get("key1") == "value1"

    def test_create_single_cache_from_config(self):
        """Test creating single cache from configuration."""
        config = {
            "cache": "aiocache.SimpleMemoryCache",
            "serializer": {
                "class": "aiocache.serializers.StringSerializer"
            },
            "namespace": "test"
        }
        
        cache = create_cache_from_dict(config)
        
        assert isinstance(cache, SimpleMemoryCache)
        assert cache.namespace == "test"
        assert isinstance(cache.serializer, StringSerializer) 