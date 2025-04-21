import inspect
from dataclasses import dataclass
from functools import partial
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
    ITaskRunner,
    ValidatorFunc,
)

T = TypeVar("T")


class Params(dict[str, tuple[str, ...]]):
    pass


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
    return partial(handler, **bound_args)


@dataclass
class TaskRunner(ITaskRunner, Generic[T]):

    encoder: IEncoder[T]
    validator: ValidatorFunc

    dispatcher: IDispatcher

    injector: DependencyInjector

    middleware: IMiddleware[T]
    router: IRouterAPI

    async def execute(self, input: bytes, addr: Any) -> tuple[str, str]:

        id, route, data = self.encoder.decode(input)

        route_pack, params = self.router.get_handler_pack(route)

        handler = route_pack.handler

        data = self.middleware.proc(data)

        obj_data = self.validator(data, route_pack.input_type)  # type: ignore

        params_handler = replace_params(handler, params)

        deps = await self.injector.resolve(params_handler)

        async def bound_handler():
            return await params_handler(obj_data, **deps)

        await self.dispatcher.dispatch(
            bound_handler,
            obj_data,
            id,
            addr,
        )

        return route, id
