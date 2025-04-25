from functools import partial
from typing import Annotated

import pytest

from serveAPI.dependencies.inject import inject
from serveAPI.dependencies.mapfunction import get_func_args


# mocks simples
class NoValidation:
    def __init__(self, default):
        self.default = default

    def validate(self, value):
        pass


class No42:
    def __init__(self, default):
        self.default = default

    def validate(self, value):
        if value == 42:
            raise ValueError


class Injectable(NoValidation):
    def validate(self, value):
        if value == "invalid":
            raise ValueError("Invalid value")


# função-alvo
def injfunc(
    a: Annotated[str, Injectable(...)],
    b: Annotated[str, Injectable(...)],
    c: int = No42(42),
    d: float = 3.14,
    e: bool = True,
):
    return a, b, c, d, e


def test_inject_by_name():
    ctx = {"a": "hello", "b": "world", "c": 123}
    injected = inject(injfunc, ctx, raise_on_missing=True, validate_default=False)
    assert isinstance(injected, partial)
    assert injected() == ("hello", "world", 123, 3.14, True)


def test_inject_by_type():
    ctx = {Injectable: "typed!", NoValidation: 42}
    injected = inject(injfunc, ctx, raise_on_missing=False, validate_default=False)
    assert injected(a="X") == ("X", "typed!", 42, 3.14, True)


def test_inject_default_used():
    ctx = {"a": "A", "b": "B"}  # 'c' será default
    injected = inject(injfunc, ctx, raise_on_missing=False, validate_default=False)
    assert injected() == ("A", "B", 42, 3.14, True)  # '...' é seu default


def test_raise_if_missing():
    ctx = {"b": "B"}  # falta 'a'
    with pytest.raises(RuntimeError):
        inject(injfunc, ctx, raise_on_missing=True, validate_default=False)


def test_validation_triggered():
    ctx = {"a": "ok", "b": "invalid"}
    with pytest.raises(ValueError):
        inject(injfunc, ctx, raise_on_missing=True, validate_default=True)


def test_falsy_values():
    ctx = {"a": "", "b": "yes", "c": 0, "d": 0.0, "e": False}
    injected = inject(injfunc, ctx, raise_on_missing=True, validate_default=False)
    assert injected() == ("", "yes", 0, 3.14, True)


def test_inject_changed_func():

    deps = get_func_args(injfunc)
    ctx = {"a": "foobar", "b": "helloworld"}
    resolfunc = inject(injfunc, ctx, False, False)
    args = get_func_args(resolfunc)
    assert args != deps


def test_inject_chained():

    deps = get_func_args(injfunc)
    ctx = {"a": "foobar"}
    resolfunc = inject(injfunc, ctx, False, False)
    args = get_func_args(resolfunc)
    assert args != deps

    ctx2 = {"b": "helloworld"}
    resolfunc2 = inject(resolfunc, ctx2, False, False)
    args2 = get_func_args(resolfunc2)
    assert args != args2

    result = resolfunc2()
    assert result == ("foobar", "helloworld", 42, 3.14, True)

    result2 = resolfunc2(c=999)
    assert result2 == ("foobar", "helloworld", 999, 3.14, True)
