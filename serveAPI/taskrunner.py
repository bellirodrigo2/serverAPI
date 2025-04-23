import inspect
from dataclasses import dataclass
from typing import (
    Annotated,
    Any,
    Callable,
    Coroutine,
    Generic,
    Mapping,
    Protocol,
    TypeVar,
    get_args,
    get_origin,
)

from serveAPI.di import DependencyInjector
from serveAPI.exceptions import (
    DependencyResolveError,
    DispatchError,
    EncoderDecodeError,
    EncoderEncodeError,
    ParamsResolveError,
    RequestMiddlewareError,
    ResponseMiddlewareError,
    RouterError,
    ServerAPIException,
    TypeCastError,
    TypeCastFromModelError,
    TypeCastToModelError,
    UnhandledError,
)
from serveAPI.interfaces import (
    Addr,
    IDispatcher,
    IEncoder,
    IExceptionRegistry,
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

    async def __call__(self, input: bytes, addr: Addr) -> None:
        Exc: type[ServerAPIException] = EncoderDecodeError
        try:
            route, data = self.encoder.decode(input)
            Exc = RouterError
            route_pack, params = self.router.get_handler_pack(route)
            Exc = RequestMiddlewareError
            data = await self.middleware.proc(data, "request")
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


class LaunchTask2(Protocol):
    def __call__(self, coro: Coroutine[Any, Any, None]) -> None: ...


class ITaskRunner2(Protocol):
    def inject_server(self, server: ISockerServer) -> None: ...
    def __call__(self, input: bytes, addr: Addr) -> None: ...


@dataclass
class TaskRunner2(ITaskRunner2, Generic[T]):
    encoder: IEncoder[T]
    cast: TypeCast[T]
    injector: DependencyInjector
    middleware: IMiddleware[T]
    router: IRouterAPI
    launcher: LaunchTask2
    exception_handlers: IExceptionRegistry
    _server: ISockerServer | None = None

    def __post_init__(self):
        if UnhandledError not in self.exception_handlers:
            raise Exception('No "UnhandledError" registered on Exception Handlers')

    def inject_server(self, server: ISockerServer) -> None:
        self._server = server

    def _resolve_exception(self, err: Exception) -> bytes:
        try:
            result = self.exception_handlers.resolve(err)
        except UnhandledError as unhandled:
            result = self.exception_handlers.resolve(unhandled)
        encoded = result.encode()
        return encoded

    def __call__(self, input: bytes, addr: Addr) -> None:
        async def task_async():
            return await self._run_task(input, addr)

        self.launcher(task_async)

    async def _run_task(self, input: bytes, addr: Addr) -> None:
        Exc: Callable[[str], ServerAPIException] | None = EncoderDecodeError
        try:
            route, data = self.encoder.decode(input)

            Exc = RouterError
            route_pack, params = self.router.get_handler_pack(route)

            Exc = RequestMiddlewareError
            data = await self.middleware.proc(data, "request")

            Exc = TypeCastToModelError
            obj_data = self.cast.to_model(data, route_pack.input_type)  # type: ignore

            Exc = ParamsResolveError
            handler = route_pack.handler
            params_bounded_handler = resolve_params_addr(handler, params, addr)

            Exc = DependencyResolveError
            deps = await self.injector.resolve(params_bounded_handler)

            # Client Function Run
            Exc = None
            response = await params_bounded_handler(obj_data, **deps)

            Exc = ResponseMiddlewareError
            response = await self.middleware.proc(response, "response")

            Exc = TypeCastFromModelError
            cast_response = self.cast.from_model(response)

            Exc = EncoderEncodeError
            encoded = self.encoder.encode(cast_response)

        except Exception as e:
            err = Exc("Error on TaskRunner") if Exc else e
            if Exc:
                err.__cause__ = e
            encoded = self._resolve_exception(err)

        if self._server is None:
            raise Exception("Server Not defined on dispatcher")
        await self._server.write(encoded, addr)  # type: ignore
