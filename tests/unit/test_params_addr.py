from typing import Annotated

import pytest

from serveAPI.interfaces import Addr, Params
from serveAPI.taskrunner import resolve_params_addr


def params_func(params: Params) -> Params:
    return params


def params_annotated_func(params: Annotated[Params, "annotated test"]) -> Params:
    return params


def params_func_str(params: Params, msg: str = "foobar") -> Params:
    return params


def params_annotated_func_str(
    params: Annotated[Params, "annotated test"], msg: str = "foobar"
) -> Params:
    return params


@pytest.mark.parametrize(
    "func",
    [params_func, params_annotated_func, params_func_str, params_annotated_func_str],
)
def test_params(func):

    olddict = {"a": "b", "c": "d"}
    newdict = {"foo": "bar", "hello": "world"}

    addr = Addr("localhost", 5555)

    new_func = resolve_params_addr(func, newdict, addr)

    retold = func(olddict)
    assert retold == olddict

    retnew = new_func()
    assert retnew == newdict
