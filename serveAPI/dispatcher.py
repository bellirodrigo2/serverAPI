from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Generic, TypeVar

from serveAPI.interfaces import (
    IDispatcher,
    IEncoder,
    IExceptionRegistry,
    IMiddleware,
    ISockerServer,
    SpawnFunc,
)
from serveAPI.safedict import SafeDict

T = TypeVar("T")


@dataclass
class Dispatcher(IDispatcher, Generic[T]):
    encoder: IEncoder[T]
    middleware: IMiddleware[T]
    spawn: SpawnFunc
    exception_handlers: IExceptionRegistry

    server: ISockerServer | None
    registry: SafeDict[str | tuple[str, int]]

    def inject_server(self, server: ISockerServer) -> None:
        self.server = server

    async def respond(
        self,
        id: str,
        addr: str | tuple[str, int] | None,
        data: bytes,
    ) -> None:

        await self.registry.pop(id)

        if addr is not None:
            # No UDP, addr é tupla (ip, porta), no TCP addr é uma string.
            if isinstance(addr, tuple):
                addr = addr[0]  # Envia só o IP
            await self.server.write(data, addr)

    async def dispatch(
        self,
        func: Callable[..., Any],
        data: Any,
        id: str,
        addr: str | tuple[str, int],
    ) -> None:

        await self.registry.set(id, addr)

        self.spawn(self._run(func, data, id, addr))

    async def _run(
        self,
        func: Callable[..., Any],
        data: Any,
        id: str,
        addr: str | tuple[str, int],
    ) -> None:
        try:
            response = await func(data)

            response = self.middleware.proc(response)

            encoded = self.encoder.encode(response)

            await self.respond(id, addr, encoded)

        except Exception as e:
            try:
                result = await self.exception_handlers.resolve(e)
                encoded = self.encoder.encode(result)
                await self.respond(id, addr, encoded)
            except Exception as inner:
                # fallback, erro no handler ou sem handler
                await self.respond(id, addr, f"Unhandled error: {str(inner)}".encode())
