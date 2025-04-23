import asyncio
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Callable, Coroutine, Generic, Type, TypeVar

from serveAPI.di import DependencyInjector
from serveAPI.interfaces import (
    IExceptionRegistry,
    IMiddleware,
    IRouterAPI,
    ISockerServer,
    LaunchTask,
)

T = TypeVar("T")


@dataclass
class App(Generic[T]):
    _server: ISockerServer
    _routers: IRouterAPI
    _middleware: IMiddleware[T]
    _exception_handler: IExceptionRegistry
    dependency_overrides: DependencyInjector
    _launcher: LaunchTask

    _lifespan: Callable[[], AbstractAsyncContextManager[None]] | None = None

    @asynccontextmanager
    async def _default_lifespan(self) -> AsyncGenerator[None, None]:
        await self._server.start()
        try:
            yield
        finally:
            await self._server.stop()

    def lifespan(
        self, func: Callable[[], AsyncGenerator[None, None]]
    ) -> Callable[[], AsyncGenerator[None, None]]:
        """Decorator para registrar lifespan customizado, igual FastAPI."""
        user_cm = asynccontextmanager(func)

        @asynccontextmanager
        async def wrapped_lifespan():
            # primeiro roda o startup padrão
            async with self._default_lifespan():
                # depois o hook do cliente
                async with user_cm():
                    yield
            # o stop() já foi chamado no finally do default

        self._lifespan = wrapped_lifespan
        return func

    async def run(self):
        """
        Resolve o lifespan (customizado ou default), entra no context manager
        e mantém o servidor rodando até shutdown.
        """
        cm = self._lifespan or self._default_lifespan
        async with cm():
            # aqui o servidor já está “up” e bloqueia até shutdown
            await asyncio.Event().wait()  # ou outra forma de esperar a parada

    # API tipo metodo... app.include_router, add_middleware, add_exception_handler
    def include_router(self, router: IRouterAPI):
        for path, handler_pack in router.items():
            self._routers.register_route(path, handler_pack.handler)

    def add_api_route(self, path: str, handler: Callable[..., Any]):
        self._routers.register_route(path, handler)

    def add_middleware(self, middleware: Callable[[T], T]) -> None:
        self._middleware.add_middleware_func(middleware)

    def add_exception_handler(
        self,
        exc_type: Type[BaseException],
        handler: Callable[[BaseException], Coroutine[Any, Any, Any]],
    ) -> None:
        """Registra diretamente um handler de exceção, como app.add_exception_handler."""
        self._exception_handler.set_handler(exc_type, handler)

    # API decorador
    def route(self, path: str):
        self._routers.route(path)

    def middleware(self):
        self._middleware.add_middleware()

    def exception_handler(
        self,
        exc_type: Type[BaseException],
    ) -> Callable[
        [Callable[[BaseException], Coroutine[Any, Any, Any]]],
        Callable[[BaseException], Coroutine[Any, Any, Any]],
    ]:
        """Usado como decorator: @app.exception_handler(...)"""
        return self._exception_handler.decorator(exc_type)
