from typing import Annotated

import pytest

from serveAPI.interfaces import IAddr, Params
from serveAPI.taskrunner import get_one_arg_name


def params_func(params: Params, addr: IAddr) -> Params:
    return params


def params_annotated_func(params: Annotated[Params, "annotated test"]) -> Params:
    return params


def params_func_str(
    params: Params,
    addr: IAddr,
    msg: str = "foobar",
) -> Params:
    return params


def params_annotated_func_str(
    params: Annotated[Params, "annotated test"],
    addr: Annotated[IAddr, "address"],
    msg: str = "foobar",
) -> Params:
    return params


@pytest.mark.parametrize(
    "func",
    [params_func, params_annotated_func, params_func_str, params_annotated_func_str],
)
def test_params(func):

    args_name = get_one_arg_name(func, Params)
    assert args_name == "params"

    addr_name = get_one_arg_name(func, IAddr)
    if func.__name__ == "params_annotated_func":
        assert addr_name is None
    else:
        assert addr_name == "addr"
