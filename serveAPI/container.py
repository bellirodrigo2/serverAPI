from typing import Any

from serveAPI import middleware
from serveAPI.di import DependencyInjector, Depends, IoCContainer
from serveAPI.dispatcher import Dispatcher
from serveAPI.exceptionhandler import ExceptionRegistry
from serveAPI.input_types.str_input import IntrusiveStrEncoder, MiddlewareStr
from serveAPI.router import RouterAPI
from serveAPI.safedict import SafeDict
from serveAPI.spawns.asyncio_spawn import AsyncioSpawn

SafeDictTaskID = SafeDict[str | tuple[str, int]]


def provide_safe_dict_dispatcher(_: IoCContainer) -> SafeDictTaskID:
    return SafeDictTaskID()


def provide_exception(_: IoCContainer) -> ExceptionRegistry:
    return ExceptionRegistry()


def provide_router(_: IoCContainer) -> RouterAPI:
    return RouterAPI()


def provide_di(_: IoCContainer) -> DependencyInjector:
    return DependencyInjector()


def make_dispatcher(
    encoder=Depends(IntrusiveStrEncoder),
    middleware=Depends(MiddlewareStr),
    spawn=Depends(AsyncioSpawn),  # aqui acho que tem que ser lambda
    exception=Depends(ExceptionRegistry),
    safedict=Depends(SafeDictTaskID),
):
    return Dispatcher[Any](
        encoder=encoder,
        middleware=middleware,
        spawn=spawn,
        exception_handlers=exception,
        server=None,
        registry=safedict,
    )


# use case
# di.resolve(make_dispatcher)
