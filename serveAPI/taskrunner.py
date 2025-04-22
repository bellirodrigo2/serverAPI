import inspect
from dataclasses import dataclass
from typing import (
    Annotated,
    Any,
    Callable,
    Generic,
    Mapping,
    TypeVar,
    get_args,
    get_origin,
)

from serveAPI.di import DependencyInjector
from serveAPI.interfaces import (
    IDispatcher,
    IEncoder,
    IMiddleware,
    IRouterAPI,
    ISockerServer,
    ITaskRunner,
    Params,
    ValidatorFunc,
)

T = TypeVar("T")


def replace_params(
    handler: Callable[..., Any], given_param: Mapping[str, str]
) -> Callable[..., Any]:
    sig = inspect.signature(handler)
    bound_args = {}

    for name, param in sig.parameters.items():
        ann = param.annotation
        if get_origin(ann) is Annotated:
            inner, *_ = get_args(ann)  # extras from Annotated
            if inner is Params:
                bound_args[name] = given_param
        elif ann is Params:
            bound_args[name] = given_param

    def bounded_handler(*args: Any, **kwargs: Any):
        final_kwargs = {**kwargs, **bound_args}
        return handler(*args, **final_kwargs)

    return bounded_handler


@dataclass
class TaskRunner(ITaskRunner, Generic[T]):

    encoder: IEncoder[T]
    validator: ValidatorFunc

    dispatcher: IDispatcher

    injector: DependencyInjector

    middleware: IMiddleware[T]
    router: IRouterAPI

    def inject_server(self, server: ISockerServer) -> None:
        self.dispatcher.inject_server(server)

    async def execute(self, input: bytes, addr: str | tuple[str, int]) -> str:

        route, data = self.encoder.decode(input)

        route_pack, params = self.router.get_handler_pack(route)
        handler = route_pack.handler

        obj_data = self.validator(data, route_pack.input_type)  # type: ignore

        data = self.middleware.proc(data, "request")

        params_bounded_handler = replace_params(handler, params)

        deps = await self.injector.resolve(params_bounded_handler)

        async def params_deps_bounded_handler():
            return await params_bounded_handler(obj_data, **deps)

        await self.dispatcher.dispatch(
            params_deps_bounded_handler,
            addr,
        )

        return route
