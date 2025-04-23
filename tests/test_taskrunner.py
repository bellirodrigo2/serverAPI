import asyncio
from typing import Any, Callable, cast
from unittest.mock import ANY

import pytest

from serveAPI.container import Dispatcher_, Middleware_
from serveAPI.di import IoCContainerSingleton
from serveAPI.exceptions import RequestMiddlewareError, RouterError
from serveAPI.interfaces import Addr, Params
from serveAPI.middleware import Middleware
from serveAPI.router import RouterAPI
from serveAPI.taskrunner import TaskRunner


def get_db():
    return "db"


def simple_func(input: str) -> str:
    return input


def params_func(input: str, params: Params) -> str:
    response = input
    for k, v in params.items():
        response += k + v
    return response


def get_routes(klist: list[tuple[str, str]] | None) -> tuple[str, str, str]:
    base = "/foobar/"
    if not klist:
        return base, base, base
    ret = (base, base, base)
    for kf, ks in klist:
        basef = ret[0]
        bases = ret[1]
        baset = ret[2]
        ret = f"{basef}{{{kf}}}/", f"{bases}{{{ks}}}/", f"{baset}{{}}/"
    return ret


def get_route(k: str | None) -> tuple[str, str]:
    base = "/foobar/"
    if k:
        return f"{base}{{k}}/", f"{base}{{}}/"
    return base, base


@pytest.mark.parametrize(
    "func, klist",
    [
        (simple_func, None),
        (params_func, [("id", "1234")]),
        (params_func, [("id", "1234"), ("user", "foobar")]),
        (
            params_func,
            [("id", "1234"), ("user", "foobar"), ("hello", "world"), ("foo", "bar")],
        ),
    ],
)
async def test_mocked_dispatch(
    mocked_dispatch_ioc: IoCContainerSingleton,
    func: Callable[[Any], Any],
    klist: list[tuple[str, str]] | None,
):

    ioc = mocked_dispatch_ioc
    router = cast(RouterAPI, ioc.resolve(RouterAPI))
    mockeddispatcher = ioc.resolve(Dispatcher_)

    taskrunner = cast(TaskRunner[str], ioc.resolve(TaskRunner))

    router_reg, router_msg, router_idx = get_routes(klist)

    router.register_route(router_reg, func)

    text = "helloworld"

    msg = f"serveAPI:{router_msg}:{text}"
    input = msg.encode()
    addr = Addr("localhost", 1234)

    return_route = await taskrunner.execute(input, addr)
    await asyncio.sleep(0.2)

    mockeddispatcher.dispatch.assert_called_with(ANY, addr)
    # args, kwargs = mockeddispatcher.dispatch.call_args

    assert return_route == router_msg

    assert router_idx in router.routes
    handler = router.routes[router_idx].handler
    assert handler == func


async def test_mocked_dispatch_no_route(
    mocked_dispatch_ioc: IoCContainerSingleton,
):

    ioc = mocked_dispatch_ioc
    mockeddispatcher = ioc.resolve(Dispatcher_)

    taskrunner = cast(TaskRunner[str], ioc.resolve(TaskRunner))

    route = "route"
    text = "helloworld"

    msg = f"serveAPI:{route}:{text}"
    input = msg.encode()
    addr = Addr("localhost", 1234)

    return_route = await taskrunner.execute(input, addr)
    await asyncio.sleep(0.2)

    mockeddispatcher.dispatch_exception.assert_called_with(ANY, addr)
    args, _ = mockeddispatcher.dispatch_exception.call_args
    assert return_route == route
    assert isinstance(args[0], RouterError)
    assert str(args[0]) == "Error on TaskRunner"


async def test_mocked_dispatch_raise_middleware(
    mocked_dispatch_ioc: IoCContainerSingleton,
):

    ioc = mocked_dispatch_ioc
    mockeddispatcher = ioc.resolve(Dispatcher_)
    middleware = cast(Middleware[Any], ioc.resolve(Middleware_))
    taskrunner = cast(TaskRunner[str], ioc.resolve(TaskRunner))

    router = cast(RouterAPI, ioc.resolve(RouterAPI))

    route = "route"
    text = "helloworld"

    def raise_func():
        raise Exception("Middleware Error")

    def func():
        return None

    router.register_route(route, func)

    middleware.add_middleware_func(raise_func, "request")

    msg = f"serveAPI:{route}:{text}"
    input = msg.encode()
    addr = Addr("localhost", 1234)

    return_route = await taskrunner.execute(input, addr)
    await asyncio.sleep(0.2)

    mockeddispatcher.dispatch_exception.assert_called_with(ANY, addr)
    args, _ = mockeddispatcher.dispatch_exception.call_args
    assert return_route == route
    assert isinstance(args[0], RequestMiddlewareError)
    assert str(args[0]) == "Error on TaskRunner"
