from unittest.mock import AsyncMock

import pytest

from serveAPI.container import Dispatcher_, get_ioc
from serveAPI.di import DependencyInjector, IoCContainer, IoCContainerSingleton
from serveAPI.exceptionhandler import ExceptionRegistry
from serveAPI.interfaces import ISockerServer
from serveAPI.middleware import Middleware
from serveAPI.router import RouterAPI

# ---------- IoC and DI ----------


@pytest.fixture
def base_container() -> IoCContainer:
    return IoCContainer()


@pytest.fixture
def singleton_container() -> IoCContainerSingleton:
    return IoCContainerSingleton()


@pytest.fixture
def injector(base_container) -> DependencyInjector:
    return DependencyInjector(container=base_container)


@pytest.fixture
def annotated_injector(singleton_container) -> DependencyInjector:
    return DependencyInjector(container=singleton_container)


# ---------- Router ----------


@pytest.fixture
def router():
    return RouterAPI(prefix="api")


@pytest.fixture
def sample_handler():
    # Exemplo de handler com parâmetros
    def handler(param1: str, param2: str) -> str:
        return f"Param1: {param1}, Param2: {param2}"

    return handler


@pytest.fixture
def sample_handler_no_params():
    # Exemplo de handler sem parâmetros
    def handler() -> str:
        return "No parameters"

    return handler


# ---------- Middleware ----------


@pytest.fixture
def simple_middleware() -> Middleware[str]:
    return Middleware[str]()


# ---------- Exception Handler ----------


@pytest.fixture
def registry() -> ExceptionRegistry:
    return ExceptionRegistry()


@pytest.fixture
def handler_called_flag():
    return {"called": False, "value": None}


@pytest.fixture
def sample_handler(handler_called_flag):
    async def handler(exc: BaseException) -> str:
        handler_called_flag["called"] = True
        handler_called_flag["value"] = str(exc)
        return f"Handled: {str(exc)}"

    return handler


# ---------- Dispatcher ----------


@pytest.fixture
async def mocked_server_ioc() -> IoCContainerSingleton:

    def provide_server_mock(_: IoCContainer):
        return AsyncMock(spec=ISockerServer)

    ioc = get_ioc()
    ioc.register(ISockerServer, provide_server_mock)

    return ioc


# ---------- TaskRunner ----------


@pytest.fixture
async def mocked_dispatch_ioc() -> IoCContainerSingleton:

    def provide_dispatch_mock(_: IoCContainer):
        return AsyncMock(spec=Dispatcher_)

    ioc = get_ioc()
    ioc.register(Dispatcher_, provide_dispatch_mock)

    return ioc
