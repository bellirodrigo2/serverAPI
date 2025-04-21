import asyncio
from dataclasses import dataclass
from typing import Any, Coroutine


@dataclass
class SyncSpawn:
    def __call__(self, coro: Coroutine[Any, Any, Any]) -> None:
        asyncio.run(coro)
