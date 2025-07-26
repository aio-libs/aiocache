import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiocache.layered import LayeredCache, create_cache_from_config, create_layered_cache, create_cache_from_dict
from aiocache.backends.memory import SimpleMemoryCache
from aiocache.serializers import StringSerializer, NullSerializer
from tests.utils import ConcreteBaseCache


class TestLayeredCache:
    """Test the LayeredCache class."""

    @pytest.fixture
    def mock_layer1(self):
        """Create a mock cache layer."""
        mock = MagicMock(spec=ConcreteBaseCache)
        mock.NAME = "mock1"
        mock.namespace = "test"
        mock.serializer = StringSerializer()
        mock.plugins = []
        mock.timeout = 5
        mock.ttl = None
        mock._build_key = lambda k, ns: f"{ns or ''}{k}"
        mock.build_key.side_effect = lambda key, namespace=None: f"{namespace or ''}{key}"
        return mock

    @pytest.fixture
    def mock_layer2(self):
        """Create a second mock cache layer."""
        mock = MagicMock(spec=ConcreteBaseCache)
        mock.NAME = "mock2"
        mock.namespace = "test"
        mock.serializer = StringSerializer()
        mock.plugins = []
        mock.timeout = 5
        mock.ttl = None
        mock._build_key = lambda k, ns: f"{ns or ''}{k}"
        mock.build_key.side_effect = lambda key, namespace=None: f"{namespace or ''}{key}"
        return mock

    @pytest.fixture
    def layered_cache(self, mock_layer1, mock_layer2):
        """Create a layered cache with two mock layers."""
        return LayeredCache([mock_layer1, mock_layer2])

    def test_init_with_empty_layers(self):
        """Test that LayeredCache raises error with empty layers."""
        with pytest.raises(ValueError, match="At least one cache layer must be provided"):
            LayeredCache([])

    def test_init_inherits_from_first_layer(self, mock_layer1, mock_layer2):
        """Test that LayeredCache inherits properties from first layer."""
        cache = LayeredCache([mock_layer1, mock_layer2])
        
        assert cache.serializer == mock_layer1.serializer
        assert cache.plugins == mock_layer1.plugins
        assert cache.namespace == mock_layer1.namespace
        assert cache.timeout == mock_layer1.timeout
        assert cache.ttl == mock_layer1.ttl

    def test_init_with_custom_kwargs(self, mock_layer1, mock_layer2):
        """Test that LayeredCache can override inherited properties."""
        custom_serializer = NullSerializer()
        cache = LayeredCache(
            [mock_layer1, mock_layer2],
            serializer=custom_serializer,
            namespace="custom"
        )
        
        assert cache.serializer == custom_serializer
        assert cache.namespace == "custom"

    async def test_get_found_in_first_layer(self, layered_cache, mock_layer1, mock_layer2):
        """Test get when value is found in first layer."""
        mock_layer1.get.return_value = "value1"
        
        result = await layered_cache.get("key1")
        
        assert result == "value1"
        mock_layer1.get.assert_called_once_with("key1", encoding="utf-8", _conn=None)
        mock_layer2.get.assert_not_called()

    async def test_get_found_in_second_layer(self, layered_cache, mock_layer1, mock_layer2):
        """Test get when value is found in second layer."""
        mock_layer1.get.return_value = None
        mock_layer2.get.return_value = "value2"
        
        result = await layered_cache.get("key1")
        
        assert result == "value2"
        mock_layer1.get.assert_called_once_with("key1", encoding="utf-8", _conn=None)
        mock_layer2.get.assert_called_once_with("key1", encoding="utf-8", _conn=None)

    async def test_get_not_found(self, layered_cache, mock_layer1, mock_layer2):
        """Test get when value is not found in any layer."""
        mock_layer1.get.return_value = None
        mock_layer2.get.return_value = None
        
        result = await layered_cache.get("key1")
        
        assert result is None
        mock_layer1.get.assert_called_once_with("key1", encoding="utf-8", _conn=None)
        mock_layer2.get.assert_called_once_with("key1", encoding="utf-8", _conn=None)

    async def test_get_layer_error_continues(self, layered_cache, mock_layer1, mock_layer2):
        """Test get continues to next layer when one layer fails."""
        mock_layer1.get.side_effect = Exception("Layer 1 error")
        mock_layer2.get.return_value = "value2"
        
        result = await layered_cache.get("key1")
        
        assert result == "value2"
        mock_layer1.get.assert_called_once_with("key1", encoding="utf-8", _conn=None)
        mock_layer2.get.assert_called_once_with("key1", encoding="utf-8", _conn=None)

    async def test_set_all_layers(self, layered_cache, mock_layer1, mock_layer2):
        """Test set writes to all layers."""
        await layered_cache.set("key1", "value1")
        
        mock_layer1.set.assert_called_once_with("key1", "value1", ttl=None, _cas_token=None, _conn=None)
        mock_layer2.set.assert_called_once_with("key1", "value1", ttl=None, _cas_token=None, _conn=None)

    async def test_set_layer_error_continues(self, layered_cache, mock_layer1, mock_layer2):
        """Test set continues when one layer fails."""
        mock_layer1.set.side_effect = Exception("Layer 1 error")
        mock_layer2.set.return_value = True
        
        result = await layered_cache.set("key1", "value1")
        
        assert result is False  # Should return False if any layer fails
        mock_layer1.set.assert_called_once()
        mock_layer2.set.assert_called_once()

    async def test_multi_get_partial_hits(self, layered_cache, mock_layer1, mock_layer2):
        """Test multi_get with partial hits across layers."""
        mock_layer1.multi_get.return_value = ["value1", None, None]
        # Layer 2 will be called with ["key2", "key3"] (the missing keys)
        mock_layer2.multi_get.return_value = ["value2", None]
        
        result = await layered_cache.multi_get(["key1", "key2", "key3"])
        
        assert result == ["value1", "value2", None]
        mock_layer1.multi_get.assert_called_once_with(["key1", "key2", "key3"], encoding="utf-8", _conn=None)
        mock_layer2.multi_get.assert_called_once_with(["key2", "key3"], encoding="utf-8", _conn=None)

    async def test_multi_set_all_layers(self, layered_cache, mock_layer1, mock_layer2):
        """Test multi_set writes to all layers."""
        pairs = [("key1", "value1"), ("key2", "value2")]
        
        await layered_cache.multi_set(pairs)
        
        mock_layer1.multi_set.assert_called_once_with(pairs, ttl=None, _conn=None)
        mock_layer2.multi_set.assert_called_once_with(pairs, ttl=None, _conn=None)

    async def test_delete_all_layers(self, layered_cache, mock_layer1, mock_layer2):
        """Test delete removes from all layers."""
        mock_layer1.delete.return_value = 1
        mock_layer2.delete.return_value = 1
        
        result = await layered_cache.delete("key1")
        
        assert result == 1
        mock_layer1.delete.assert_called_once_with("key1", _conn=None)
        mock_layer2.delete.assert_called_once_with("key1", _conn=None)

    async def test_multi_delete_all_layers(self, layered_cache, mock_layer1, mock_layer2):
        """Test multi_delete removes from all layers."""
        keys = ["key1", "key2"]
        mock_layer1.multi_delete.return_value = 2
        mock_layer2.multi_delete.return_value = 1
        
        result = await layered_cache.multi_delete(keys)
        
        assert result == 2  # Should return max count
        mock_layer1.multi_delete.assert_called_once_with(keys, _conn=None)
        mock_layer2.multi_delete.assert_called_once_with(keys, _conn=None)

    async def test_exists_any_layer(self, layered_cache, mock_layer1, mock_layer2):
        """Test exists returns True if key exists in any layer."""
        mock_layer1.exists.return_value = False
        mock_layer2.exists.return_value = True
        
        result = await layered_cache.exists("key1")
        
        assert result is True
        mock_layer1.exists.assert_called_once_with("key1", _conn=None)
        mock_layer2.exists.assert_called_once_with("key1", _conn=None)

    async def test_increment_all_layers(self, layered_cache, mock_layer1, mock_layer2):
        """Test increment updates all layers."""
        mock_layer1.increment.return_value = 5
        mock_layer2.increment.return_value = 5
        
        result = await layered_cache.increment("key1", delta=1)
        
        assert result == 5
        mock_layer1.increment.assert_called_once_with("key1", delta=1, _conn=None)
        mock_layer2.increment.assert_called_once_with("key1", delta=1, _conn=None)

    async def test_clear_all_layers(self, layered_cache, mock_layer1, mock_layer2):
        """Test clear clears all layers."""
        await layered_cache.clear()
        
        mock_layer1.clear.assert_called_once_with(namespace=None, _conn=None)
        mock_layer2.clear.assert_called_once_with(namespace=None, _conn=None)

    async def test_raw_first_layer_only(self, layered_cache, mock_layer1, mock_layer2):
        """Test raw command only executes on first layer."""
        mock_layer1._raw.return_value = "result"

        result = await layered_cache.raw("command", "arg1")

        assert result == "result"
        mock_layer1._raw.assert_called_once_with("command", "arg1", encoding="utf-8", _conn=None)
        mock_layer2._raw.assert_not_called()

    async def test_context_manager(self, mock_layer1, mock_layer2):
        """Test context manager enters and exits all layers."""
        cache = LayeredCache([mock_layer1, mock_layer2])
        
        async with cache:
            pass
        
        mock_layer1.__aenter__.assert_called_once()
        mock_layer1.__aexit__.assert_called_once()
        mock_layer2.__aenter__.assert_called_once()
        mock_layer2.__aexit__.assert_called_once()


class TestCacheFactory:
    """Test the cache factory functions."""

    def test_create_cache_from_config_memory(self):
        """Test creating a memory cache from config."""
        config = {
            "cache": "aiocache.SimpleMemoryCache",
            "serializer": {
                "class": "aiocache.serializers.StringSerializer"
            }
        }
        
        cache = create_cache_from_config(config)
        
        assert isinstance(cache, SimpleMemoryCache)
        assert isinstance(cache.serializer, StringSerializer)

    def test_create_cache_from_config_with_kwargs(self):
        """Test creating a cache with additional kwargs."""
        config = {
            "cache": "aiocache.SimpleMemoryCache",
            "namespace": "test",
            "timeout": 10
        }
        
        cache = create_cache_from_config(config)
        
        assert isinstance(cache, SimpleMemoryCache)
        assert cache.namespace == "test"
        assert cache.timeout == 10.0

    def test_create_layered_cache(self):
        """Test creating a layered cache from configs."""
        configs = [
            {
                "cache": "aiocache.SimpleMemoryCache",
                "serializer": {
                    "class": "aiocache.serializers.StringSerializer"
                }
            },
            {
                "cache": "aiocache.SimpleMemoryCache",
                "serializer": {
                    "class": "aiocache.serializers.NullSerializer"
                }
            }
        ]
        
        cache = create_layered_cache(configs)
        
        assert isinstance(cache, LayeredCache)
        assert len(cache.layers) == 2
        assert isinstance(cache.layers[0], SimpleMemoryCache)
        assert isinstance(cache.layers[1], SimpleMemoryCache)

    def test_create_cache_from_dict_single(self):
        """Test creating a single cache from dict."""
        config = {
            "cache": "aiocache.SimpleMemoryCache",
            "namespace": "test"
        }
        
        cache = create_cache_from_dict(config)
        
        assert isinstance(cache, SimpleMemoryCache)
        assert cache.namespace == "test"

    def test_create_cache_from_dict_layered(self):
        """Test creating a layered cache from dict."""
        config = {
            "layers": [
                {
                    "cache": "aiocache.SimpleMemoryCache",
                    "serializer": {
                        "class": "aiocache.serializers.StringSerializer"
                    }
                }
            ],
            "namespace": "test"
        }
        
        cache = create_cache_from_dict(config)
        
        assert isinstance(cache, LayeredCache)
        assert cache.namespace == "test"
        assert len(cache.layers) == 1

    def test_create_cache_from_dict_invalid(self):
        """Test creating cache from invalid dict raises error."""
        config = {"invalid": "config"}
        
        with pytest.raises(ValueError, match="Configuration must contain either 'cache' or 'layers' key"):
            create_cache_from_dict(config) 