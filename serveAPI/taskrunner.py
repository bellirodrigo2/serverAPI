from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from serveAPI.di import DependencyInjector, IoCContainer
from serveAPI.interfaces import (
    IDispatcher,
    IEncoder,
    IMiddleware,
    IRouterAPI,
    ITaskRunner,
)

T = TypeVar("T")


@dataclass
class TaskRunner(ITaskRunner[T]):

    encoder: IEncoder[T]
    validator: Callable[[T, type[T]], T]

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
    ) -> IoCContainer:
        return self.injector.container

    async def execute(self, input: bytes, addr: Any) -> tuple[str, str]:

        id, route, data = self.encoder.decode(input)

        route_pack = self.router.get_handler_pack(route)
        handler = route_pack.handler

        data = self.middleware.proc(data)

        obj_data = self.validator(data, route_pack.input_type)  # type: ignore

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
