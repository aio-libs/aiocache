import pytest
import asyncio

from aiocache.backends import SimpleMemoryBackend


@pytest.fixture
def memory(event_loop):
    b = SimpleMemoryBackend()
    yield b

    event_loop.run_until_complete(b._clear())


class TestSimpleMemoryBackend:

    @pytest.mark.asyncio
    async def test_no_ttl_no_handle(self, memory):
        await memory._set(pytest.KEY, "value", ttl=0)
        assert pytest.KEY not in memory._handlers

        await memory._set(pytest.KEY, "value")
        assert pytest.KEY not in memory._handlers

    @pytest.mark.asyncio
    async def test_ttl_handle_cancelled(self, memory, mocker):
        await memory._set(pytest.KEY, "value", ttl=100)
        assert pytest.KEY in memory._handlers
        assert isinstance(memory._handlers[pytest.KEY], asyncio.Handle)

        mocker.spy(SimpleMemoryBackend, '_handlers')

        await memory._delete(pytest.KEY)
        assert memory._handlers.get.return_value.cancel.call_count == 1
        assert pytest.KEY not in memory._handlers
