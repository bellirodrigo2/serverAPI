import asyncio
from typing import Any, Callable, Coroutine

from serveAPI.di import IoCContainer

asyncio_spawn = asyncio.create_task

AsyncioSpawn = Callable[[Coroutine[Any, Any, Any]], asyncio.Task[Any]]


def provide_spawn(
    _: IoCContainer,
) -> AsyncioSpawn:
    return asyncio_spawn
