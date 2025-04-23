import asyncio
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Generic, TypeVar

from serveAPI.exceptions import (
    EncoderEncodeError,
    ResponseMiddlewareError,
    UnhandledError,
)
from serveAPI.interfaces import (
    Addr,
    IDispatcher,
    IEncoder,
    IExceptionRegistry,
    IMiddleware,
    ISockerServer,
    LaunchTask,
)

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
        addr: Addr,
    ) -> None:
        ondone = partial(self._ondone, addr=addr)
        self.launcher(func, ondone)

    async def dispatch_exception(self, err: Exception, addr: Addr):
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

    async def _ondone(self, fut: asyncio.Future[Any], addr: Addr):
        Exc: type[Exception] | None = None
        try:
            if fut.cancelled():
                raise Exception("Coroutine cancelled!")
            response = fut.result()
            Exc = ResponseMiddlewareError
            response = await self.middleware.proc(response, "response")

            Exc = EncoderEncodeError
            encoded = self.encoder.encode(response)

        except Exception as e:
            err = Exc("Error on dispatch callback") if Exc else e
            if Exc:
                err.__cause__ = e
            encoded = self._resolve_exception(err)

        await self._respond(addr, encoded)

    async def _respond(
        self,
        addr: Addr,
        data: bytes,
    ) -> None:
        if self._server is None:
            raise Exception("Server Not defined on dispatcher")
        await self._server.write(data, addr)  # type: ignore
