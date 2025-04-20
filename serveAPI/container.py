from serveAPI.di import DependencyInjector, IoCContainer
from serveAPI.exceptionhandler import ExceptionRegistry
from serveAPI.router import RouterAPI
from serveAPI.safedict import SafeDict


def provide_safe_dict_dispatcher(_: IoCContainer) -> SafeDict[str | tuple[str, int]]:
    return SafeDict[str | tuple[str, int]]()


def provide_exception(_: IoCContainer) -> ExceptionRegistry:
    return ExceptionRegistry()


def provide_router(_: IoCContainer) -> RouterAPI:
    return RouterAPI()


def provide_di(_: IoCContainer) -> DependencyInjector:
    return DependencyInjector()
