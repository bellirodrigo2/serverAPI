from typing import Any

from serveAPI import middleware
from serveAPI.di import DependencyInjector, IoCContainer
from serveAPI.dispatcher import Dispatcher
from serveAPI.encoder import IntrusiveHeaderEncoder
from serveAPI.exceptionhandler import ExceptionRegistry
from serveAPI.router import RouterAPI
from serveAPI.safedict import SafeDict
from serveAPI.spawns.asyncio_spawn import AsyncioSpawn, ProvideSpawn

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

SafeDict_ = SafeDict[Any]


def provide_dispatcher(container: IoCContainer) -> Dispatcher[Any]:
    encoder = container.resolve(Encoder_)
    middleware = container.resolve(Middleware_)
    spawn = container.resolve(AsyncioSpawn)
    exception = container.resolve(ExceptionRegistry)
    safedict = container.resolve(SafeDict_)

    return Dispatcher[Any](
        encoder=encoder,
        middleware=middleware,
        spawn=spawn,
        exception_handlers=exception,
        server=None,
        registry=safedict,
    )
