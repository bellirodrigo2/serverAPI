import asyncio
from typing import Any, Callable, Coroutine

from serveAPI.ioc import IoCContainer

asyncio_spawn = asyncio.create_task


def provide_spawn(
    _: IoCContainer,
) -> Callable[[Coroutine[Any, Any, Any]], asyncio.Task[Any]]:
    return asyncio_spawn
