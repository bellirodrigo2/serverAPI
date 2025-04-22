import asyncio
from dataclasses import dataclass
from typing import Any, Callable

from serveAPI.di import IoCContainer
from serveAPI.interfaces import LaunchTask


@dataclass
class AsyncioLauncher(LaunchTask):
    def __call__(
        self, func: Callable[[], Any], cb: Callable[..., Any] | None = None
    ) -> None:
        task = asyncio.create_task(func())
        if cb is not None:
            task.add_done_callback(lambda fut: asyncio.create_task(cb(fut)))


def provide_asyncio_launcher(_: IoCContainer) -> AsyncioLauncher:
    return AsyncioLauncher()
