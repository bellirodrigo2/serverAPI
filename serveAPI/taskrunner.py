import inspect
from dataclasses import dataclass
from typing import (
    Annotated,
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterator,
    Mapping,
    Protocol,
    Sequence,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

from serveAPI.di import DependencyInjector
from serveAPI.exceptions import (
    DependencyResolveError,
    EncoderDecodeError,
    EncoderEncodeError,
    ParamsResolveError,
    RequestMiddlewareError,
    ResponseMiddlewareError,
    RouterError,
    ServerAPIException,
    TypeCastFromModelError,
    TypeCastToModelError,
    UnhandledError,
)
from serveAPI.interfaces import (
    Depends,
    IAddr,
    IEncoder,
    IExceptionRegistry,
    IMiddleware,
    IMiddlewareFunc,
    IRouterAPI,
    ISockerServer,
    ITaskRunner,
    LaunchTask,
    Params,
    TypeCast,
)

T = TypeVar("T")


def get_one_arg_name(handler: Callable[..., Any], arg_type: type) -> str | None:
    sig = inspect.signature(handler)

    for name, param in sig.parameters.items():
        ann = param.annotation
        if get_origin(ann) is Annotated:
            inner, *_ = get_args(ann)  # extras from Annotated
            if inner is arg_type:
                return name
        elif ann is arg_type:
            return name
    return None


def get_all_arg_name(
    handler: Callable[..., Any], arg_type: type
) -> Sequence[str] | None:
    sig = inspect.signature(handler)

    args_names: list[str] = []

    for name, param in sig.parameters.items():
        ann = param.annotation
        if get_origin(ann) is Annotated:
            inner, *_ = get_args(ann)  # extras from Annotated
            if inner is arg_type:
                args_names.append(name)
        elif ann is arg_type:
            args_names.append(name)
    return None


@dataclass
class TaskRunner(ITaskRunner, Generic[T]):
    encoder: IEncoder[T]
    cast: TypeCast[T]
    injector: DependencyInjector
    middleware: IMiddleware[T]
    router: IRouterAPI
    launcher: LaunchTask
    exception_handlers: IExceptionRegistry
    fire_forget: bool = False
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

    def __call__(self, input: bytes, addr: IAddr) -> None:
        self.launcher(self._run_task(input, addr))

    async def _run_task(self, input: bytes, addr: IAddr) -> None:
        Exc: Callable[[str], ServerAPIException] | None = EncoderDecodeError
        try:
            route, data = self.encoder.decode(input)

            Exc = RouterError
            route_pack, params = self.router.get_handler_pack(route)

            Exc = RequestMiddlewareError
            data = await self.middleware.proc(data, "request")

            Exc = TypeCastToModelError
            obj_data = self.cast.to_model(data, route_pack.input_type)

            Exc = ParamsResolveError
            kwargs: dict[str, Any] = {}
            handler = route_pack.handler
            params_arg = get_one_arg_name(handler, Params)
            if params_arg:
                kwargs[params_arg] = params
            addr_arg = get_one_arg_name(handler, IAddr)
            if addr_arg:
                kwargs[addr_arg] = addr

            Exc = DependencyResolveError
            deps = await self.injector.resolve(handler)
            kwargs = {**kwargs, **deps}

            # Client Function Run
            Exc = None
            response: Any | None = await handler(obj_data, **kwargs)

            if response is None:
                return

            Exc = ResponseMiddlewareError
            response = await self.middleware.proc(response, "response")

            if self.fire_forget:
                return

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
        await self._server.write(encoded, addr)


class IMiddleware2(Protocol[T]):

    def __iter__(self) -> Iterator[IMiddlewareFunc[T]]: ...
    def add(self, middleware: IMiddlewareFunc[T]) -> IMiddlewareFunc[T]: ...
    def use(self) -> Callable[[IMiddlewareFunc[T]], IMiddlewareFunc[T]]: ...
    async def run(self, data: T, final_handler: Callable[[T], Awaitable[T]]) -> T: ...


def get_params_addr(handler: Callable[..., Any], params: Params, addr: IAddr):
    kwargs: dict[str, Any] = {}
    params_arg = get_one_arg_name(handler, Params)
    if params_arg:
        kwargs[params_arg] = params
    addr_arg = get_one_arg_name(handler, IAddr)
    if addr_arg:
        kwargs[addr_arg] = addr
    return kwargs


@dataclass
class TaskRunner2(ITaskRunner, Generic[T]):
    encoder: IEncoder[T]
    cast: TypeCast[T]
    injector: DependencyInjector
    middleware: IMiddleware2[T]
    router: IRouterAPI
    launcher: LaunchTask
    exception_handlers: IExceptionRegistry
    fire_forget: bool = False
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

    def __call__(self, input: bytes, addr: IAddr) -> None:
        self.launcher(self._run_task(input, addr))

    async def _run_task(self, input: bytes, addr: IAddr) -> None:
        Exc: Callable[[str], ServerAPIException] | None = EncoderDecodeError
        try:
            route, data = self.encoder.decode(input)

            Exc = RouterError
            route_pack, params = self.router.get_handler_pack(route)
            handler = route_pack.handler

            Exc = None
            context: dict[Any, Any] = {Params: params, IAddr: addr}
            await self.injector.run_validate_dependencies(
                route_pack.dependencies, context
            )

            Exc = TypeCastToModelError
            obj_data = self.cast.to_model(data, route_pack.input_type)

            Exc = ParamsResolveError
            kwargs: dict[str, Any] = get_params_addr(handler, params, addr)

            Exc = DependencyResolveError
            deps = await self.injector.resolve(handler)
            kwargs = {**kwargs, **deps}

            async def bound_handler(data: T):
                return await handler(data, **kwargs)

            # Client Function Run
            response = await self._run_middlewares(
                obj_data, bound_handler, params, addr
            )

            if response is None:
                return

            if self.fire_forget:
                return

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
        await self._server.write(encoded, addr)

    async def _run_middlewares(
        self,
        data: T,
        handler: Callable[..., Any],
        params: Params,
        addr: IAddr,
    ) -> T:
        """Executa os middlewares e chama o handler final após a cadeia de middlewares."""
        handler_chain = handler  # Inicia com o handler final

        for middleware in self.middleware:

            kwargs: dict[str, Any] = get_params_addr(middleware, params, addr)
            deps = await self.injector.resolve(middleware)
            kwargs = {**kwargs, **deps}

            # early binding
            async def wrapped(
                data: T, _mw=middleware, _next=handler_chain, _kwargs=kwargs
            ):
                return await _mw(input=data, call_next=_next, **_kwargs)

            # Atualiza o handler_chain com o middleware
            handler_chain = wrapped

        # Executa a cadeia de middlewares e o handler final
        return await handler_chain(data)
