import asyncio
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Generic, TypeVar

from serveAPI.exceptions import UnhandledError
from serveAPI.interfaces import (
    IDispatcher,
    IEncoder,
    IExceptionRegistry,
    IMiddleware,
    ISockerServer,
    LaunchTask,
)

# from serveAPI.safedict import SafeDict

T = TypeVar("T")


@dataclass
class Dispatcher(IDispatcher, Generic[T]):
    encoder: IEncoder[T]
    middleware: IMiddleware[T]
    launcher: LaunchTask
    exception_handlers: IExceptionRegistry

    _server: ISockerServer | None = None

    def inject_server(self, server: ISockerServer) -> None:
        self.server = server

    async def dispatch(
        self,
        func: Callable[[], Any],
        addr: str | tuple[str, int],
    ) -> None:

        ondone = partial(self._ondone, addr=addr)
        self.launcher(func, ondone)

    async def dispatch_exception(self, err: Exception, addr: str | tuple[str, int]):

        encoded = self._resolve_exception(err)

        async def bonded_response():
            return await self._respond(addr, encoded)

        self.launcher(bonded_response, None)
        # await self._respond(addr, encoded)

    def _resolve_exception(self, err: Exception) -> bytes:
        try:
            result = self.exception_handlers.resolve(err)
        except UnhandledError as unhandled:
            result = self.exception_handlers.resolve(unhandled)
        encoded = result.encode()
        return encoded

    async def _ondone(self, fut: asyncio.Future[Any], addr: str | tuple[str, int]):
        try:

            if fut.cancelled():
                raise Exception("Coroutine cancelled!")
            response = fut.result()
            response = self.middleware.proc(response, "response")
            encoded = self.encoder.encode(response)
        except Exception as e:
            encoded = self._resolve_exception(e)

        await self._respond(addr, encoded)

    async def _respond(
        self,
        addr: str | tuple[str, int] | None,
        data: bytes,
    ) -> None:

        if addr is not None:
            # No UDP, addr é tupla (ip, porta), no TCP addr é uma string.
            if isinstance(addr, tuple):
                addr = addr[0]  # Envia só o IP

            if self._server is None:
                raise Exception("Server Not defined on dispatcher")

            await self._server.write(data, addr)  # type: ignore
