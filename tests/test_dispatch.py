import pytest

from serveAPI.container import Dispatcher_


def test_dispatch(server_mocked_dispatch: Dispatcher_):

    dispatcher = server_mocked_dispatch
    # dispatcher.dispatch()
