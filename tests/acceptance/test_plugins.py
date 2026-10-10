import asyncio
from typing import OrderedDict

import pytest

from aiocache.plugins import BasePlugin, HitMissRatioPlugin, TimingPlugin


class TestHitMissRatioPlugin:
    @pytest.mark.parametrize(
        "stored, default_style, value",
        [
            pytest.param(False, "omitted", None, id="missing-omitted-default"),
            pytest.param(False, "positional", "fallback", id="missing-positional-default"),
            pytest.param(False, "keyword", "fallback", id="missing-keyword-default"),
            pytest.param(True, "omitted", None, id="stored-none"),
            pytest.param(True, "keyword", False, id="stored-false-default-false"),
            pytest.param(True, "keyword", object(), id="stored-identical-default"),
            pytest.param(True, "omitted", "value", id="ordinary-hit"),
        ],
    )
    async def test_get_actual_hit(self, memory_cache, stored, default_style, value):
        memory_cache.plugins = [HitMissRatioPlugin()]
        if stored:
            await memory_cache.set("key", value)

        if default_style == "positional":
            result = await memory_cache.get("key", value)
        elif default_style == "keyword":
            result = await memory_cache.get("key", default=value)
        else:
            result = await memory_cache.get("key")

        assert result is value
        assert memory_cache.hit_miss_ratio == {
            "total": 1,
            "hits": int(stored),
            "hit_ratio": int(stored),
        }

    @pytest.mark.parametrize("timeout", (0, 5))
    async def test_get_concurrent_hit_state(self, memory_cache, timeout):
        entered = asyncio.Event()
        release = asyncio.Event()

        class WaitForOtherRead(BasePlugin):
            async def post_get(self, client, key, took=0, ret=None):
                if key == "hit":
                    entered.set()
                    await release.wait()

        memory_cache.timeout = timeout
        memory_cache.plugins = [WaitForOtherRead(), HitMissRatioPlugin()]
        await memory_cache.set("hit", None)

        hit_task = asyncio.create_task(memory_cache.get("hit"))
        try:
            await asyncio.wait_for(entered.wait(), 1)
            assert await memory_cache.get("miss") is None
        finally:
            release.set()
            await hit_task

        assert memory_cache.hit_miss_ratio == {"total": 2, "hits": 1, "hit_ratio": 0.5}

    @pytest.mark.parametrize("outer_hit", (False, True))
    async def test_get_nested_hit_state(self, memory_cache, outer_hit):
        class NestedRead(BasePlugin):
            # Deliberately keep the existing hook signature without **kwargs.
            async def post_get(self, client, key, took=0, ret=None):
                if key == "outer":
                    assert await client.get("inner", timeout=0) is None

        memory_cache.plugins = [NestedRead(), HitMissRatioPlugin()]
        await memory_cache.set("outer" if outer_hit else "inner", None)

        assert await memory_cache.get("outer", timeout=0) is None
        assert memory_cache.hit_miss_ratio == {"total": 2, "hits": 1, "hit_ratio": 0.5}

    @pytest.mark.parametrize("error", (RuntimeError, asyncio.CancelledError))
    async def test_get_failed_hook_clears_hit_state(self, memory_cache, error):
        class FailedHook(BasePlugin):
            async def post_get(self, client, key, took=0, ret=None):
                raise error()

        plugin = HitMissRatioPlugin()
        memory_cache.plugins = [FailedHook(), plugin]
        await memory_cache.set("hit", None)

        with pytest.raises(error):
            await memory_cache.get("hit", timeout=0)

        # A standalone hook call must not inherit the failed read's hit state.
        await plugin.post_get(memory_cache, "miss", ret=None)
        assert memory_cache.hit_miss_ratio == {"total": 1, "hits": 0, "hit_ratio": 0}

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
        memory_cache._cache = OrderedDict(data)

        for key in keys:
            await memory_cache.get(key)

        hits = [x for x in keys if "test" + x in data]
        assert memory_cache.hit_miss_ratio["hits"] == len(hits)
        assert (
            memory_cache.hit_miss_ratio["hit_ratio"]
            == len(hits) / memory_cache.hit_miss_ratio["total"]
        )

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
        memory_cache._cache = OrderedDict(data)

        for key in keys:
            await memory_cache.multi_get([key])

        hits = [x for x in keys if "test" + x in data]
        assert memory_cache.hit_miss_ratio["hits"] == len(hits)
        assert (
            memory_cache.hit_miss_ratio["hit_ratio"]
            == len(hits) / memory_cache.hit_miss_ratio["total"]
        )

    async def test_set_and_get_using_namespace(self, memory_cache):
        memory_cache.plugins = [HitMissRatioPlugin()]
        key = "A"
        namespace = "test"
        value = 1
        await memory_cache.set(key, value, namespace=namespace)
        result = await memory_cache.get(key, namespace=namespace)
        assert result == value


class TestTimingPlugin:
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
        memory_cache._cache = OrderedDict(data)

        for key in keys:
            await memory_cache.get(key)

        assert "get_max" in memory_cache.profiling
        assert "get_min" in memory_cache.profiling
        assert "get_total" in memory_cache.profiling
        assert "get_avg" in memory_cache.profiling
