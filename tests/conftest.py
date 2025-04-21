import pytest

from serveAPI.di import DependencyInjector, IoCContainer, IoCContainerSingleton
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
