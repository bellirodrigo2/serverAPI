import pytest

from serveAPI.middleware import Middleware


def test_add_middleware_func(simple_middleware: Middleware[str]):
    def uppercase(data: str) -> str:
        return data.upper()

    simple_middleware.add_middleware_func(uppercase, "request")

    result = simple_middleware.proc("testando", "request")
    assert result == "TESTANDO"


def test_add_middleware_decorator(simple_middleware: Middleware[str]):
    @simple_middleware.add_middleware("request")
    def add_prefix(data: str) -> str:
        return "PREFIX_" + data

    result = simple_middleware.proc("data", "request")
    assert result == "PREFIX_data"


def test_multiple_middlewares_execution_order(simple_middleware: Middleware[str]):
    @simple_middleware.add_middleware("response")
    def step1(data: str) -> str:
        return data.strip()

    @simple_middleware.add_middleware("response")
    def step2(data: str) -> str:
        return data.lower()

    @simple_middleware.add_middleware("response")
    def step3(data: str) -> str:
        return f"[{data}]"

    result = simple_middleware.proc("   TESTE   ", "response")
    assert result == "[teste]"


def test_proc_without_middlewares_returns_input(simple_middleware: Middleware[str]):
    result = simple_middleware.proc("unchanged", "request")
    assert result == "unchanged"


def test_add_middleware_func_returns_same_function(simple_middleware: Middleware[str]):
    def identity(data: str) -> str:
        return data

    returned = simple_middleware.add_middleware_func(identity, "request")
    assert returned is identity


def test_proc_with_middleware_that_removes_data(simple_middleware: Middleware[str]):
    @simple_middleware.add_middleware("response")
    def erase(data: str) -> str:
        return ""

    result = simple_middleware.proc("something", "response")
    assert result == ""
