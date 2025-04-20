from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Generic, MutableMapping, Type, TypeVar

from serveAPI.interfaces import IRouterAPI, ISockerServer, ITaskRunner

T = TypeVar("T")


async def ServerAPI(
    runner: ITaskRunner[T],
    make_server: Callable[[ITaskRunner[T]], ISockerServer],
):
    server = make_server(runner)
    runner.inject_server(server)
    await server.start()
    return Server(runner, server)


@dataclass
class Server(Generic[T]):
    runner: ITaskRunner[T]
    server: ISockerServer

    @property
    def dependency_overrides(
        self,
    ) -> MutableMapping[Callable[..., Any], Callable[..., Any]]:
        return self.runner.overrides

    # API tipo metodo... app.include_router, add_middleware, add_exception_handler
    def include_router(self, router: IRouterAPI):

        tr_routers = self.runner.routers

        for path, handler_pack in router.items():
            tr_routers.register_route(path, handler_pack.handler)

    def add_middleware(
        self, middleware: Callable[[MutableMapping[str, Any]], MutableMapping[str, Any]]
    ) -> None:
        tr_middleware = self.runner.middlewares

    def add_exception_handler(
        self,
        exc_type: Type[BaseException],
        handler: Callable[[BaseException], Coroutine[Any, Any, Any]],
    ):
        self.exception_handlers.add_handler(exc_type, handler)

    # API decorador
    def route(self, path: str):
        tr_routers = self.runner.routers
        tr_routers.add_route(path)

    def middleware(
        self,
    ): ...

    def exception_handler(self, exc_type: Type[BaseException]):
        return self.exception_handlers.decorator(exc_type)
