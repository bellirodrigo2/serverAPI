from dataclasses import dataclass
from typing import Any, Callable, MutableMapping, TypeVar

from serveAPI.di import DependencyInjector, resolve_dependencies
from serveAPI.interfaces import (
    IDispatcher,
    IEncoder,
    IMiddleware,
    IRouterAPI,
    ITaskRunner,
    ITypeValidator,
)

T = TypeVar("T")


@dataclass
class TaskRunner(ITaskRunner[T]):

    encoder: IEncoder[T]
    validator: ITypeValidator

    dispatcher: IDispatcher

    injector: DependencyInjector

    middleware: IMiddleware[T]
    router: IRouterAPI

    @property
    def routers(self) -> IRouterAPI:
        return self.router

    @property
    def middlewares(self) -> IMiddleware[T]:
        return self.middleware

    @property
    def overrides(
        self,
    ) -> MutableMapping[Callable[..., Any], Callable[..., Any]]:
        return self.injector.overrides

    async def execute(self, input: bytes, addr: Any) -> tuple[str, str]:

        id, route, data = self.encoder.decode(input)

        route_pack = self.router.get_handler_pack(route)
        handler = route_pack.handler

        data = self.middleware.proc(data)

        obj_data = self.validator.validate_input(data, route_pack.input_type)  # type: ignore

        deps = await self.injector.resolve(handler)

        async def bound_handler():
            return await handler(obj_data, **deps)

        await self.dispatcher.dispatch(
            bound_handler,
            obj_data,
            id,
            addr,
        )

        return route, id
