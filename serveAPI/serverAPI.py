from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, MutableMapping, Type
from uuid import uuid4

from serveAPI.interfaces import ISocketRouter, ITaskRunner
from serveAPI.tcpserver import TCPServer
from serveAPI.udpserver import UDPServer


@dataclass
class ServerAPI:
    host: str
    port: int
    runner: ITaskRunner
    fire_and_forget: bool
    spawn: Callable[[Coroutine[Any, Any, Any]], None]

    makeid: Callable[[], str] = field(default=lambda: str(uuid4()))

    server_type: str = field(default="tcp")  # Usando string ('tcp' ou 'udp')

    # FALTA ACESSO A ROUTER, MIDDLEWARE e exception que vem do taskrunner

    # API tipo metodo... app.include_router, add_middleware, add_exception_handler
    def include_router(self, router: ISocketRouter):
        # TODO AQUI VAI TER QUE ADICIONAR O DICT DESSE ROUTER COM O ROUTER GERAL DO IHANDLER
        ...

    def add_middleware(
        self, middleware: Callable[[MutableMapping[str, Any]], MutableMapping[str, Any]]
    ) -> None: ...

    def add_exception_handler(
        self,
        exc_type: Type[BaseException],
        handler: Callable[[BaseException], Coroutine[Any, Any, Any]],
    ):
        self.exception_handlers.add_handler(exc_type, handler)

    # API decorador
    def route(self, path: str): ...

    def middleware(
        self,
    ): ...

    def exception_handler(self, exc_type: Type[BaseException]):
        return self.exception_handlers.decorator(exc_type)

    async def __post_init__(self):
        await self._start()

    async def _start(self):
        if self.server_type == "tcp":
            server = TCPServer(
                host=self.host,
                port=self.port,
                runner=self.runner,
                fire_and_forget=self.fire_and_forget,
                makeid=self.makeid,
            )
        elif self.server_type == "udp":
            server = UDPServer(
                host=self.host,
                port=self.port,
                runner=self.runner,
                fire_and_forget=self.fire_and_forget,
                makeid=self.makeid,
                spawn=self.spawn,
            )
        else:
            raise Exception(f'Server Type "{self.server_type}" is Unknown')
        await server.start()
