import asyncio
from typing import Any
from uuid import uuid4

from serveAPI import middleware
from serveAPI.datatypes.str_input import (
    provide_str_hashed_encoder,
    provide_str_middleware,
    provide_str_simple_encoder,
)
from serveAPI.di import DependencyInjector, IoCContainer, IoCContainerSingleton
from serveAPI.dispatcher import Dispatcher
from serveAPI.encoder import NonIntrusiveHeaderEncoder
from serveAPI.exceptionhandler import ExceptionRegistry
from serveAPI.exceptions import (
    DependencyResolveError,
    DispatchError,
    EncoderDecodeError,
    EncoderEncodeError,
    ParamsResolveError,
    RequestMiddlewareError,
    ResponseMiddlewareError,
    RouterError,
    TypeCastError,
    UnhandledError,
    internal_exception_handler,
)
from serveAPI.interfaces import ISockerServer, LaunchTask, TypeCast
from serveAPI.router import RouterAPI
from serveAPI.safedict import SafeDict
from serveAPI.serverAPI import App
from serveAPI.servers.tcpserver import TCPServer
from serveAPI.spawns.asyncio_launcher import provide_asyncio_launcher
from serveAPI.taskrunner import TaskRunner, TaskRunner2


def provide_exception(_: IoCContainer) -> ExceptionRegistry:
    er = ExceptionRegistry()

    er.set_handler(EncoderEncodeError, internal_exception_handler)
    er.set_handler(EncoderDecodeError, internal_exception_handler)
    er.set_handler(RouterError, internal_exception_handler)
    er.set_handler(TypeCastError, internal_exception_handler)
    er.set_handler(RequestMiddlewareError, internal_exception_handler)
    er.set_handler(ResponseMiddlewareError, internal_exception_handler)
    er.set_handler(ParamsResolveError, internal_exception_handler)
    er.set_handler(DependencyResolveError, internal_exception_handler)
    er.set_handler(DispatchError, internal_exception_handler)
    er.set_handler(UnhandledError, handler=internal_exception_handler)

    return er


def provide_router(_: IoCContainer) -> RouterAPI:
    return RouterAPI()


def provide_di(_: IoCContainer) -> DependencyInjector:
    return DependencyInjector()


Encoder_ = NonIntrusiveHeaderEncoder[Any]
Middleware_ = middleware.Middleware[Any]

Dispatcher_ = Dispatcher[Any]


def provide_dispatcher(container: IoCContainer) -> Dispatcher_:
    encoder = container.resolve(Encoder_)
    middleware = container.resolve(Middleware_)
    launcher = container.resolve(LaunchTask)
    exception = container.resolve(ExceptionRegistry)
    none_server = container.resolve(ISockerServer)

    return Dispatcher[Any](
        encoder=encoder,
        middleware=middleware,
        launcher=launcher,
        exception_handlers=exception,
        _server=none_server,
        # registry=safedict,
    )


def provide_taskrunner(container: IoCContainer) -> TaskRunner[Any]:
    encoder = container.resolve(Encoder_)
    dispatcher = container.resolve(Dispatcher_)
    di = container.resolve(DependencyInjector)
    middleware = container.resolve(Middleware_)
    router = container.resolve(RouterAPI)
    cast = container.resolve(TypeCast)

    return TaskRunner(
        encoder=encoder,
        dispatcher=dispatcher,
        injector=di,
        middleware=middleware,
        router=router,
        cast=cast,
    )


def provide_taskrunner2(container: IoCContainer) -> TaskRunner2[Any]:
    encoder = container.resolve(Encoder_)
    cast = container.resolve(TypeCast)
    di = container.resolve(DependencyInjector)
    middleware = container.resolve(Middleware_)
    router = container.resolve(RouterAPI)
    launcher = container.resolve(LaunchTask)
    exception = container.resolve(ExceptionRegistry)
    none_server = container.resolve(ISockerServer)

    return TaskRunner2(
        encoder=encoder,
        cast=cast,
        injector=di,
        middleware=middleware,
        router=router,
        launcher=launcher,
        exception_handlers=exception,
        _server=none_server,
    )


SafeDictStreamWriter = SafeDict[asyncio.StreamWriter]


def provide_safe_dict_server(_: IoCContainer) -> SafeDictStreamWriter:
    return SafeDictStreamWriter()


class MakeID:
    def __call__(self) -> str:
        return str(uuid4())


def provide_makeid(_: IoCContainer) -> MakeID:
    return MakeID()


def provide_none_server(_: IoCContainer) -> None:
    return None


def get_base_ioc():
    ioc = IoCContainerSingleton()

    ioc.register(SafeDictStreamWriter, provide_safe_dict_server)
    ioc.register(ExceptionRegistry, provide_exception)
    ioc.register(RouterAPI, provide_router)
    ioc.register(DependencyInjector, provide_di)
    ioc.register(LaunchTask, provide_asyncio_launcher)
    ioc.register(MakeID, provide_makeid)

    ioc.register(Dispatcher_, provide_dispatcher)

    ioc.register(TaskRunner, provide_taskrunner)
    ioc.register(TaskRunner2, provide_taskrunner2)

    ioc.register(ISockerServer, provide_none_server)
    return ioc


def get_str_ioc():
    ioc = get_base_ioc()
    ioc.register(TypeCast, lambda _: None)
    ioc.register(Middleware_, provide_str_middleware)

    return ioc


def get_simple_str_ioc():
    ioc = get_str_ioc()
    ioc.register(Encoder_, provide_str_simple_encoder)

    return ioc


def get_hashed_str_ioc():
    ioc = get_str_ioc()
    ioc.register(Encoder_, provide_str_hashed_encoder)
    return ioc


def ServerAPI(host: str, port: int, fire_and_forget: bool):
    ioc = get_str_ioc()
    taskrunner = ioc.resolve(TaskRunner)
    makeid = ioc.resolve(MakeID)
    server = TCPServer(
        host=host,
        port=port,
        runner=taskrunner,
        fire_and_forget=fire_and_forget,
        makeid=makeid,
    )
    taskrunner.inject_server(server)
    router = ioc.resolve(RouterAPI)
    middleware = ioc.resolve(Middleware_)
    er = ioc.resolve(ExceptionRegistry)
    do = ioc.resolve(DependencyInjector)
    launcher = ioc.resolve(LaunchTask)

    app = App(
        _server=server,
        _routers=router,
        _middleware=middleware,
        _exception_handler=er,
        dependency_overrides=do,
        _launcher=launcher,
    )
    return app
