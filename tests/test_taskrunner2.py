import asyncio
import json
from typing import Any, Callable, cast
from unittest.mock import ANY

import pytest

from serveAPI.container import Dispatcher_, Middleware_
from serveAPI.di import IoCContainerSingleton
from serveAPI.exceptions import RequestMiddlewareError, RouterError
from serveAPI.interfaces import Addr, ISockerServer, Params
from serveAPI.middleware import Middleware
from serveAPI.router import RouterAPI
from serveAPI.taskrunner import ITaskRunner2, TaskRunner, TaskRunner2


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
    taskrunner2_mockedserver_ioc: IoCContainerSingleton,
    func: Callable[[Any], Any],
    klist: list[tuple[str, str]] | None,
):

    ioc = taskrunner2_mockedserver_ioc
    router = cast(RouterAPI, ioc.resolve(RouterAPI))
    mockedserver = ioc.resolve(ISockerServer)

    taskrunner = cast(TaskRunner2[str], ioc.resolve(TaskRunner2))

    router_reg, router_msg, router_idx = get_routes(klist)

    router.register_route(router_reg, func)

    text = "helloworld"

    msg = f"serveAPI:{router_msg}:{text}"
    input = msg.encode()
    addr = Addr("localhost", 1234)

    taskrunner(input, addr)
    await asyncio.sleep(0.2)

    mockedserver.write.assert_called_with(ANY, addr)
    # args, kwargs = mockeddispatcher.dispatch.call_args

    assert router_idx in router.routes
    handler = router.routes[router_idx].handler
    assert handler == func


async def test_mocked_dispatch_no_route(
    taskrunner2_mockedserver_ioc: IoCContainerSingleton,
):

    ioc = taskrunner2_mockedserver_ioc
    mockedserver = ioc.resolve(ISockerServer)

    taskrunner = cast(TaskRunner2[str], ioc.resolve(TaskRunner2))

    route = "route"
    text = "helloworld"

    msg = f"serveAPI:{route}:{text}"
    input = msg.encode()
    addr = Addr("localhost", 1234)

    taskrunner(input, addr)
    await asyncio.sleep(0.2)

    mockedserver.write.assert_called_with(ANY, addr)
    args, _ = mockedserver.write.call_args

    err = json.loads(args[0].decode())
    assert err["Exception"]["Type"] == "RouterError"
    assert err["Exception"]["Msg"] == "Error on TaskRunner"
    assert err["OriginalException"]["Type"] == "Exception"
    assert "not found on RouterAPI" in err["OriginalException"]["Msg"]


async def test_mocked_dispatch_raise_middleware(
    taskrunner2_mockedserver_ioc: IoCContainerSingleton,
):
    ioc = taskrunner2_mockedserver_ioc
    middleware = cast(Middleware[Any], ioc.resolve(Middleware_))
    taskrunner = cast(TaskRunner2[str], ioc.resolve(TaskRunner2))

    router = cast(RouterAPI, ioc.resolve(RouterAPI))
    mockedserver = ioc.resolve(ISockerServer)

    route = "route"
    text = "helloworld"

    class ThisError(Exception):
        pass

    def raise_func(_: Any):
        raise ThisError("Middleware Error")

    def func():
        return None

    router.register_route(route, func)

    middleware.add_middleware_func(raise_func, "request")

    msg = f"serveAPI:{route}:{text}"
    input = msg.encode()
    addr = Addr("localhost", 1234)

    taskrunner(input, addr)
    await asyncio.sleep(0.2)

    mockedserver.write.assert_called_with(ANY, addr)
    args, _ = mockedserver.write.call_args
    err = json.loads(args[0].decode())
    assert err["Exception"]["Type"] == "RequestMiddlewareError"
    assert err["Exception"]["Msg"] == "Error on TaskRunner"
    assert err["OriginalException"]["Type"] == "ThisError"
    assert "Middleware Error" in err["OriginalException"]["Msg"]
    print(err)
