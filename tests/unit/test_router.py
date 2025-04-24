from typing import Annotated, Any, Callable

import pytest

from serveAPI.router import (
    HandlerPack,
    PathValidationError,
    RouterAPI,
    extract_path_params,
)


@pytest.mark.parametrize(
    "path, expected",
    [
        ("/path1/", ((), "/path1/")),
        ("path", ((), "/path/")),
        ("path1/", ((), "/path1/")),
        ("/path1/{id}", (("id",), "/path1/{}/")),
        ("/path1/{id}/{user}", (("id", "user"), "/path1/{}/{}/")),
        ("/path1/{id}/path2/{user}", (("id", "user"), "/path1/{}/path2/{}/")),
    ],
)
def test_path_param(path: str, expected: tuple[tuple[str, ...], str] | None):
    param, npath = extract_path_params(path)
    assert param == expected[0]
    assert npath == expected[1]


@pytest.mark.parametrize(
    "path,expected_handler_params",
    [
        ("/api/{param1}/{param2}", ("param1", "param2")),
        ("/api/{param1}/", ("param1",)),
        ("/api/", ()),
    ],
)
def test_register_route_with_params(
    router: RouterAPI, path: str, expected_handler_params: tuple[str, ...]
):
    def handler(data: Annotated[dict, "body"]):
        return f"Data: {data}"

    router.register_route(path, handler)
    route_pack, _ = router.get_handler_pack(path)

    assert isinstance(route_pack, HandlerPack)
    assert route_pack.handler == handler
    assert route_pack.params == expected_handler_params


@pytest.mark.parametrize(
    "path,params_input,expected_output,handler_factory",
    [
        (
            "/api/{param1}/{param2}",
            ["value1", "value2"],
            "Data: {'param1': 'value1', 'param2': 'value2'}",
            lambda: lambda data: f"Data: {data}",
        ),
    ],
)
def test_execute_with_params(
    router: RouterAPI,
    path: str,
    params_input: list[str],
    expected_output: str,
    handler_factory: Callable[[], Callable[..., Any]],
):
    handler = handler_factory()
    router.register_route(path, handler)
    route_pack, params = router.get_handler_pack(path)
    model_input = dict(zip(route_pack.params, params_input))
    result = route_pack.handler(model_input)
    assert result == expected_output


@pytest.mark.parametrize(
    "path,expected_output",
    [("/api/", "No parameters")],
)
def test_execute_no_params(router: RouterAPI, path: str, expected_output: str):
    def handler(_: dict) -> str:
        return "No parameters"

    router.register_route(path, handler)
    route_pack, _ = router.get_handler_pack(path)
    result = route_pack.handler({})
    assert result == expected_output


def test_path_validation(router: RouterAPI):
    router.register_route("/api/valid_path", lambda _: "ok")
    with pytest.raises(PathValidationError):
        router.register_route("/api/invalid@path", lambda _: "bad")


def test_get_handler_pack_with_valid_route(router: RouterAPI):
    def handler(data: Annotated[dict, "body"]):
        return data

    router.register_route("/api/{param1}", handler)
    route_pack, params = router.get_handler_pack("/api/{value1}")

    assert route_pack.handler == handler
    assert params == {"param1": "value1"}


def test_get_handler_pack_with_invalid_route(router: RouterAPI):
    router.register_route("/api/{param1}", lambda data: data)
    with pytest.raises(Exception):
        router.get_handler_pack("/api/invalid")


def test_route_with_dynamic_path(router: RouterAPI):
    def handler(data: Annotated[dict, "body"]):
        return data

    router.register_route("/api/{param1}/{param2}", handler)
    route_pack, params = router.get_handler_pack("/api/{value1}/{value2}")
    assert params == {"param1": "value1", "param2": "value2"}
    assert route_pack.handler == handler


def test_route_registration_type_hints(router: RouterAPI):
    def handler(data: Annotated[str, "body"]) -> str:
        return f"{data}"

    router.register_route("/api/{param1}", handler)
    route_pack, _ = router.get_handler_pack("/api/{value1}")
    assert route_pack.input_type == str
