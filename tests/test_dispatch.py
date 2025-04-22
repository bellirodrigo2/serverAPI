import asyncio

import pytest

from serveAPI.container import Dispatcher_
from serveAPI.di import IoCContainerSingleton
from serveAPI.interfaces import ISockerServer


async def test_dispatch(mocked_server_ioc: IoCContainerSingleton):

    ioc = mocked_server_ioc
    mockserver = ioc.resolve(ISockerServer)
    dispatcher = ioc.resolve(Dispatcher_)

    async def func():
        return "hello" + "world"

    addr = "addr123"  # ('addr123', 80)

    resp = await func()
    respbytes = resp.encode()

    await dispatcher.dispatch(func, addr)
    await asyncio.sleep(0.2)

    mockserver.write.assert_called_with(respbytes, addr)
