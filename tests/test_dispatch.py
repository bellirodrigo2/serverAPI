import asyncio
from unittest.mock import ANY, Mock

from serveAPI.container import Dispatcher_
from serveAPI.di import IoCContainerSingleton
from serveAPI.interfaces import Addr, ISockerServer


# @pytest.mark.parametrize(
#     "func",
#     [
#     ],
# )
async def test_dispatch(mocked_server_ioc: IoCContainerSingleton):
    ioc = mocked_server_ioc
    mockserver = ioc.resolve(ISockerServer)
    dispatcher = ioc.resolve(Dispatcher_)

    innermocker = Mock()

    async def func():
        innermocker.run()
        return "hello" + "world"

    addr = Addr("localhost", 1234)  # ('addr123', 80)
    respbytes = "helloworld".encode()

    await dispatcher.dispatch(func, addr)
    await asyncio.sleep(0.2)

    mockserver.write.assert_called_with(respbytes, addr)
    innermocker.run.assert_called_once()


async def test_dispatch_raise_func(mocked_server_ioc: IoCContainerSingleton):
    ioc = mocked_server_ioc
    mockserver = ioc.resolve(ISockerServer)
    dispatcher = ioc.resolve(Dispatcher_)

    async def func():
        raise Exception("helloworld")

    addr = Addr("localhost", 1234)  # ('addr123', 80)

    await dispatcher.dispatch(func, addr)
    await asyncio.sleep(0.2)

    mockserver.write.assert_called_with(ANY, addr)
    args, _ = mockserver.write.call_args

    err_msg = args[0].decode()
    assert "Exception" in err_msg
    assert "UnhandledError" in err_msg
    assert "OriginalException" in err_msg
    assert "helloworld" in err_msg
