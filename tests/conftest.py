from typing import Annotated, Any, Callable, Mapping, Optional, Union
from unittest.mock import AsyncMock

import pytest

from serveAPI.container import get_simple_str_ioc
from serveAPI.dependencies.model import Injectable
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
def sample_handler() -> Callable[..., str]:
    def handler(data: Annotated[dict, "body"]) -> str:
        return f"Data: {data}"

    return handler


@pytest.fixture
def sample_handler_no_params() -> Callable[[], str]:
    def handler(_: Annotated[dict, "body"]) -> str:
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

    ioc = get_simple_str_ioc()
    ioc.register(ISockerServer, provide_server_mock)

    return ioc


@pytest.fixture
async def mocked_dispatch_ioc() -> IoCContainerSingleton:
    def provide_dispatch_mock(_: IoCContainer):
        return AsyncMock(spec=Dispatcher_)

    ioc = get_simple_str_ioc()
    ioc.register(Dispatcher_, provide_dispatch_mock)

    return ioc


@pytest.fixture
async def taskrunner2_mockedserver_ioc() -> IoCContainerSingleton:

    def provide_server_mock(_: IoCContainer):
        return AsyncMock(spec=ISockerServer)

    ioc = get_simple_str_ioc()

    ioc.register(ISockerServer, provide_server_mock)

    return ioc


# -------------------- DEPENDENCIES


def func_mt() -> None:
    pass


def func_simple(arg1: str, arg2: int) -> None:
    pass


def func_def(arg1: str = "foobar", arg2: int = 12, arg3=True, arg4=None) -> None:  # type: ignore
    pass


def func_ann(
    arg1: Annotated[str, "meta1"],
    arg2: Annotated[int, "meta1", 2],
    arg3: Annotated[list[str], "meta1", 2, True],
    arg4: Annotated[dict[str, Any], "meta1", 2, True] = {"foo": "bar"},
) -> None:
    pass


def func_mix(arg1, arg2: Annotated[str, "meta1"], arg3: str, arg4="foobar") -> None:
    pass


@pytest.fixture
def funcsmap() -> Mapping[str, Callable[..., Any]]:

    funcs_map: dict[str, Callable[..., Any]] = {
        "mt": func_mt,
        "simple": func_simple,
        "def": func_def,
        "ann": func_ann,
        "mix": func_mix,
    }

    return funcs_map


def func_annotated_none(
    arg1: Annotated[Optional[str], "meta"],
    arg2: Annotated[Optional[int], "meta2"] = None,
) -> None:
    pass


def func_union(
    arg1: Union[int, str],
    arg2: Optional[float] = None,
) -> None:
    pass


def func_varargs(*args: int, **kwargs: str) -> None:
    pass


def func_kwonly(*, arg1: int, arg2: str = "default") -> None:
    pass


class MyClass:
    pass


def func_forward(arg: "MyClass") -> None:
    pass


def func_none_default(arg: Optional[str] = None) -> None:
    pass


@pytest.fixture
def funcsmap_extended() -> Mapping[str, Callable[..., Any]]:
    return {
        "annotated_none": func_annotated_none,
        "union": func_union,
        "varargs": func_varargs,
        "kwonly": func_kwonly,
        "forward": func_forward,
        "none_default": func_none_default,
    }


# ----------- INJECT


def inj_func(
    arg: str, arg_ann: Annotated[str, Injectable(...)], arg_dep: str = Injectable(...)
):
    pass


@pytest.fixture
def injfunc():
    return inj_func
