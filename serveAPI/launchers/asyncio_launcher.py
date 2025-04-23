import asyncio
from dataclasses import dataclass
from typing import Any, Coroutine

from serveAPI.di import IoCContainer
from serveAPI.interfaces import LaunchTask


@dataclass
class AsyncioLauncher(LaunchTask):
    def __call__(self, coro: Coroutine[Any, Any, None]) -> None:
        asyncio.create_task(coro)


def provide_asyncio_launcher(_: IoCContainer) -> AsyncioLauncher:
    return AsyncioLauncher()
