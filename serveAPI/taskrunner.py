from dataclasses import dataclass
from typing import Any, TypeVar

from serveAPI.di import resolve_dependencies
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

    middleware: IMiddleware[T]
    router: IRouterAPI

    @property
    def routers(self) -> IRouterAPI:
        return self.router

    @property
    def middlewares(self) -> IMiddleware[T]:
        return self.middleware

    async def execute(self, input: bytes, addr: Any) -> tuple[str, str]:

        id, route, data = self.encoder.decode(input)

        route_pack = self.router.get_handler_pack(route)
        handler = route_pack.handler

        data = self.middleware.proc(data)

        obj_data = self.validator.validate_input(data, route_pack.input_type)  # type: ignore

        deps = await resolve_dependencies(handler)

        async def bound_handler():
            return await handler(obj_data, **deps)

        await self.dispatcher.dispatch(
            bound_handler,
            obj_data,
            id,
            addr,
        )

        return route, id
