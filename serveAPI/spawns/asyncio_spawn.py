import asyncio
from dataclasses import dataclass
from typing import Any, Coroutine

from serveAPI.di import IoCContainer
from serveAPI.interfaces import SpawnFunc


@dataclass
class AsyncioSpawn(SpawnFunc):
    def __call__(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Task[Any]:
        return asyncio.create_task(coro)


def provide_spawn(_: IoCContainer) -> AsyncioSpawn:
    return AsyncioSpawn()
