import pytest

from aiocache.backends.memory import SimpleMemoryBackend
from aiocache.plugins import HitMissRatioPlugin, TimingPlugin


class TestHitMissRatioPlugin:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "data, ratio",
        [
            ({"testa": 1, "testb": 2, "testc": 3}, 0.6),
            ({"testa": 1, "testz": 0}, 0.2),
            ({}, 0),
            ({"testa": 1, "testb": 2, "testc": 3, "testd": 4, "teste": 5}, 1),
        ],
    )
    async def test_get_hit_miss_ratio(self, memory_cache, data, ratio):
        keys = ["a", "b", "c", "d", "e", "f"]
        memory_cache.plugins = [HitMissRatioPlugin()]
        SimpleMemoryBackend._cache = data

        for key in keys:
            await memory_cache.get(key)

        hits = [x for x in keys if "test" + x in data]
        assert memory_cache.hit_miss_ratio["hits"] == len(hits)
        assert (
            memory_cache.hit_miss_ratio["hit_ratio"]
            == len(hits) / memory_cache.hit_miss_ratio["total"]
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "data, ratio",
        [
            ({"testa": 1, "testb": 2, "testc": 3}, 0.6),
            ({"testa": 1, "testz": 0}, 0.2),
            ({}, 0),
            ({"testa": 1, "testb": 2, "testc": 3, "testd": 4, "teste": 5}, 1),
        ],
    )
    async def test_multi_get_hit_miss_ratio(self, memory_cache, data, ratio):
        keys = ["a", "b", "c", "d", "e", "f"]
        memory_cache.plugins = [HitMissRatioPlugin()]
        SimpleMemoryBackend._cache = data

        for key in keys:
            await memory_cache.multi_get([key])

        hits = [x for x in keys if "test" + x in data]
        assert memory_cache.hit_miss_ratio["hits"] == len(hits)
        assert (
            memory_cache.hit_miss_ratio["hit_ratio"]
            == len(hits) / memory_cache.hit_miss_ratio["total"]
        )

    @pytest.mark.asyncio
    async def test_set_and_get_using_namespace(self, memory_cache):
        memory_cache.plugins = [HitMissRatioPlugin()]
        key = "A"
        namespace = "test"
        value = 1
        await memory_cache.set(key, value, namespace=namespace)
        result = await memory_cache.get(key, namespace=namespace)
        assert result == value


class TestTimingPlugin:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "data, ratio",
        [
            ({"testa": 1, "testb": 2, "testc": 3}, 0.6),
            ({"testa": 1, "testz": 0}, 0.2),
            ({}, 0),
            ({"testa": 1, "testb": 2, "testc": 3, "testd": 4, "teste": 5}, 1),
        ],
    )
    async def test_get_avg_min_max(self, memory_cache, data, ratio):
        keys = ["a", "b", "c", "d", "e", "f"]
        memory_cache.plugins = [TimingPlugin()]
        SimpleMemoryBackend._cache = data

        for key in keys:
            await memory_cache.get(key)

        assert "get_max" in memory_cache.profiling
        assert "get_min" in memory_cache.profiling
        assert "get_total" in memory_cache.profiling
        assert "get_avg" in memory_cache.profiling
