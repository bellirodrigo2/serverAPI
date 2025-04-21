import asyncio
from typing import Any
from uuid import uuid4

from serveAPI import middleware
from serveAPI.di import DependencyInjector, IoCContainer, IoCContainerSingleton
from serveAPI.dispatcher import Dispatcher
from serveAPI.encoder import IntrusiveHeaderEncoder
from serveAPI.exceptionhandler import ExceptionRegistry
from serveAPI.input_types.str_input import (
    provide_str_intrusive_encoder,
    provide_str_middleware,
    provide_str_validator,
)
from serveAPI.interfaces import ValidatorFunc
from serveAPI.router import RouterAPI
from serveAPI.safedict import SafeDict
from serveAPI.serverAPI import App
from serveAPI.servers.tcpserver import TCPServer
from serveAPI.spawns.asyncio_spawn import AsyncioSpawn, provide_spawn
from serveAPI.taskrunner import TaskRunner

SafeDictTaskID = SafeDict[str | tuple[str, int]]


def provide_safe_dict_dispatcher(_: IoCContainer) -> SafeDictTaskID:
    return SafeDictTaskID()


def provide_exception(_: IoCContainer) -> ExceptionRegistry:
    return ExceptionRegistry()


def provide_router(_: IoCContainer) -> RouterAPI:
    return RouterAPI()


def provide_di(_: IoCContainer) -> DependencyInjector:
    return DependencyInjector()


Encoder_ = IntrusiveHeaderEncoder[Any]
Middleware_ = middleware.Middleware[Any]

Dispatcher_ = Dispatcher[Any]


def provide_dispatcher(container: IoCContainer) -> Dispatcher_:
    encoder = container.resolve(Encoder_)
    middleware = container.resolve(Middleware_)
    spawn = container.resolve(AsyncioSpawn)
    exception = container.resolve(ExceptionRegistry)
    safedict = container.resolve(SafeDictTaskID)

    return Dispatcher[Any](
        encoder=encoder,
        middleware=middleware,
        spawn=spawn,
        exception_handlers=exception,
        server=None,
        registry=safedict,
    )


def provide_taskrunner(container: IoCContainer) -> TaskRunner[Any]:
    encoder = container.resolve(Encoder_)
    dispatcher = container.resolve(Dispatcher_)
    di = container.resolve(DependencyInjector)
    middleware = container.resolve(Middleware_)
    router = container.resolve(RouterAPI)
    validator = container.resolve(ValidatorFunc)

    return TaskRunner(
        encoder=encoder,
        dispatcher=dispatcher,
        injector=di,
        middleware=middleware,
        router=router,
        validator=validator,
    )


SafeDictStreamWriter = SafeDict[asyncio.StreamWriter]


def provide_safe_dict_server(_: IoCContainer) -> SafeDictStreamWriter:
    return SafeDictStreamWriter()


ioc = IoCContainerSingleton()

ioc.register(SafeDictTaskID, provide_safe_dict_dispatcher)
ioc.register(SafeDictStreamWriter, provide_safe_dict_server)
ioc.register(ExceptionRegistry, provide_exception)
ioc.register(RouterAPI, provide_router)
ioc.register(DependencyInjector, provide_di)
ioc.register(Middleware_, provide_str_middleware)
ioc.register(Encoder_, provide_str_intrusive_encoder)
ioc.register(AsyncioSpawn, provide_spawn)
ioc.register(ValidatorFunc, provide_str_validator)

ioc.register(Dispatcher_, provide_dispatcher)

ioc.register(TaskRunner, provide_taskrunner)


def ServerAPI(host: str, port: int, fire_and_forget: bool):
    taskrunner = ioc.resolve(TaskRunner)
    server = TCPServer(
        host=host,
        port=port,
        runner=taskrunner,
        fire_and_forget=fire_and_forget,
        makeid=lambda: str(uuid4()),
    )
    router = ioc.resolve(RouterAPI)
    middleware = ioc.resolve(Middleware_)
    er = ioc.resolve(ExceptionRegistry)
    do = ioc.resolve(DependencyInjector)
    return App(
        _server=server,
        _routers=router,
        _middleware=middleware,
        _exception_handler=er,
        dependency_overrides=do,
    )
