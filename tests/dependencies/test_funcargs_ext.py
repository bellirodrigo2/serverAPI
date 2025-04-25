from typing import Optional, Union

from serveAPI.dependencies.mapfunction import NO_DEFAULT, get_func_args
from tests.conftest import MyClass


def test_annotated_none(funcsmap_extended):
    args = get_func_args(funcsmap_extended["annotated_none"])
    assert len(args) == 2
    assert args[0].name == "arg1"
    assert args[0].basetype == Optional[str]
    assert args[0].extras == ["meta"]
    assert args[1].default is None
    assert args[1].hasinstance(int) is False


def test_union(funcsmap_extended):
    args = get_func_args(funcsmap_extended["union"])
    assert len(args) == 2
    assert args[0].argtype == Union[int, str]
    assert args[0].default == NO_DEFAULT
    assert args[1].default is None
    assert args[1].basetype == Optional[float] or args[1].argtype == Optional[float]


def test_varargs(funcsmap_extended):
    args = get_func_args(funcsmap_extended["varargs"])
    assert len(args) == 2
    assert args[0].name == "args"
    assert args[1].name == "kwargs"


def test_kwonly(funcsmap_extended):
    args = get_func_args(funcsmap_extended["kwonly"])
    assert len(args) == 2
    assert args[0].name == "arg1"
    assert args[0].default == NO_DEFAULT
    assert args[1].default == "default"


def test_forward(funcsmap_extended):
    args = get_func_args(funcsmap_extended["forward"])
    assert len(args) == 1
    assert args[0].name == "arg"
    assert args[0].basetype == MyClass


def test_none_default(funcsmap_extended):
    args = get_func_args(funcsmap_extended["none_default"])
    assert len(args) == 1
    assert args[0].name == "arg"
    assert args[0].default is None
    assert args[0].basetype == Optional[str] or args[0].argtype == Optional[str]


def get_db(db_name: str): ...


def get_token(outro_arg: str, token: str = Route(...)):
    return token


def get_user(arg: str, token: str = Depends(get_token), db=Depends(get_db)):
    return {"user": f"User with token {token}"}


def get_data(user: dict = Depends(get_user)):
    return {"data": f"data for {user['user']}"}
