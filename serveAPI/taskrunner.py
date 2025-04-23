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
from serveAPI.exceptions import (
    DependencyResolveError,
    DispatchError,
    EncoderDecodeError,
    ParamsResolveError,
    RequestMiddlewareError,
    RouterError,
    ServerAPIException,
    TypeCastError,
)
from serveAPI.interfaces import (
    Addr,
    IDispatcher,
    IEncoder,
    IMiddleware,
    IRouterAPI,
    ISockerServer,
    ITaskRunner,
    Params,
    TypeCast,
)

T = TypeVar("T")


def resolve_params_addr(
    handler: Callable[..., Any],
    given_param: Mapping[str, str],
    given_addr: Addr,
) -> Callable[..., Any]:
    sig = inspect.signature(handler)
    bound_args: dict[str, Any] = {}

    for name, param in sig.parameters.items():
        ann = param.annotation
        if get_origin(ann) is Annotated:
            inner, *_ = get_args(ann)  # extras from Annotated
            if inner is Params:
                bound_args[name] = given_param
            elif inner is Addr:
                bound_args[name] = given_addr
        elif ann is Params:
            bound_args[name] = given_param
        elif ann is Addr:
            bound_args[name] = given_addr

    def bounded_handler(*args: Any, **kwargs: Any):
        final_kwargs = {**kwargs, **bound_args}
        return handler(*args, **final_kwargs)

    return bounded_handler


@dataclass
class TaskRunner(ITaskRunner, Generic[T]):

    encoder: IEncoder[T]
    cast: TypeCast[T] | None

    dispatcher: IDispatcher

    injector: DependencyInjector

    middleware: IMiddleware[T]
    router: IRouterAPI

    def inject_server(self, server: ISockerServer) -> None:
        self.dispatcher.inject_server(server)

    async def execute(self, input: bytes, addr: Addr) -> str:

        route: str | None = None

        Exc: type[ServerAPIException] = EncoderDecodeError
        try:
            route, data = self.encoder.decode(input)
            Exc = RouterError
            route_pack, params = self.router.get_handler_pack(route)
            Exc = RequestMiddlewareError
            data = self.middleware.proc(data, "request")
            if self.cast:
                Exc = TypeCastError
                obj_data = self.cast.to_model(data, route_pack.input_type)  # type: ignore
            else:
                obj_data = data
            Exc = ParamsResolveError
            handler = route_pack.handler
            params_bounded_handler = resolve_params_addr(handler, params, addr)
            Exc = DependencyResolveError
            deps = await self.injector.resolve(params_bounded_handler)

            async def params_deps_bounded_handler():
                return await params_bounded_handler(obj_data, **deps)

            Exc = DispatchError
            await self.dispatcher.dispatch(
                params_deps_bounded_handler,
                addr,
            )

        except Exception as e:
            err = Exc("Error on TaskRunner")
            err.__cause__ = e
            await self.dispatcher.dispatch_exception(err, addr)

        return route or "UnkownRoute"
