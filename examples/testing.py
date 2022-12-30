import asyncio
from unittest.mock import MagicMock

from aiocache.base import BaseCache


async def main():
    mocked_cache = MagicMock(spec=BaseCache)
    mocked_cache.get.return_value = "world"
    print(await mocked_cache.get("hello"))


if __name__ == "__main__":
    asyncio.run(main())
