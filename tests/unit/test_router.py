from typing import Any, Callable

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


# Fixture para criar instâncias de RouterAPI e Handlers
@pytest.fixture
def router():
    return RouterAPI(prefix="api")


@pytest.fixture
def sample_handler() -> Callable[..., str]:
    # Exemplo de handler com parâmetros
    def handler(param1: str, param2: str) -> str:
        return f"Param1: {param1}, Param2: {param2}"

    return handler


@pytest.fixture
def sample_handler_no_params() -> Callable[[], str]:
    # Exemplo de handler sem parâmetros
    def handler() -> str:
        return "No parameters"

    return handler


def str_arg_func(_: str):
    return "foobar"


# Teste de registro de rota com parâmetros
@pytest.mark.parametrize(
    "path,expected_handler_params",
    [
        ("/api/{param1}/{param2}", ("param1", "param2")),
        ("/api/{param1}/", ("param1",)),
        ("/api/", ()),
    ],
)
def test_register_route_with_params(
    router: RouterAPI,
    path: str,
    expected_handler_params: tuple[str, ...],
    sample_handler,
):
    router.register_route(path, sample_handler)

    # Verifica se o handler foi registrado corretamente
    route_pack, params = router.get_handler_pack(path)

    assert isinstance(route_pack, HandlerPack)
    assert route_pack.handler == sample_handler
    assert route_pack.params == expected_handler_params


# Teste de execução com parâmetros
@pytest.mark.parametrize(
    "path,params_input,expected_output,handler_factory",
    [
        (
            "/api/{param1}/{param2}",
            ["value1", "value2"],
            "Param1: value1, Param2: value2",
            lambda: lambda param1, param2: f"Param1: {param1}, Param2: {param2}",
        ),
        (
            "/api/{param1}/",
            ["value1"],
            "Param1: value1, Param2: None",
            lambda: lambda param1: f"Param1: {param1}, Param2: None",
        ),
        (
            "/api/",
            [],
            "No parameters",
            lambda: lambda: "No parameters",
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

    result = route_pack.handler(*params_input)

    assert result == expected_output


# Teste de validação de caminho
@pytest.mark.parametrize(
    "path,should_fail",
    [
        ("api/valid_path", False),
        ("api/{param1}", False),
        ("api/{param1}/{param2}", False),
        ("api/invalid@path", True),
        ("api/{param1}/invalid@path", True),
    ],
)
def test_path_validation(router: RouterAPI, path: str, should_fail: bool):
    if should_fail:
        with pytest.raises(PathValidationError):
            router.register_route(path, lambda param1: None)
    else:
        router.register_route(path, lambda param1: None)  # Não deve levantar erro


# Teste de recuperação de handler e parâmetros
def test_get_handler_pack_with_valid_route(router: RouterAPI, sample_handler):
    router.register_route("/api/{param1}", sample_handler)

    route_pack, params = router.get_handler_pack("/api/{value1}")

    assert route_pack.handler == sample_handler
    assert params == {"param1": "value1"}


def test_get_handler_pack_with_invalid_route(router: RouterAPI):
    router.register_route("/api/{param1}", lambda param1: None)

    with pytest.raises(Exception):
        router.get_handler_pack("/api/invalid")


# Teste de execução sem parâmetros
@pytest.mark.parametrize(
    "path,expected_output",
    [("/api/", "No parameters"), ("/api/another", "No parameters")],
)
def test_execute_no_params(
    router: RouterAPI, path: str, expected_output: str, sample_handler_no_params
):
    router.register_route(path, sample_handler_no_params)

    # Simula a obtenção do handler com base na rota
    route_pack, params = router.get_handler_pack(path)
    handler = route_pack.handler

    # Invoca o handler
    result = handler()

    assert result == expected_output


# Teste de rota com parâmetros obrigatórios e path dinâmico
def test_route_with_dynamic_path(router: RouterAPI, sample_handler):
    # Registra a rota
    router.register_route("/api/{param1}/{param2}", sample_handler)

    # Testa a rota dinâmica
    route_pack, params = router.get_handler_pack("/api/{value1}/{value2}")
    assert params == {"param1": "value1", "param2": "value2"}
    assert route_pack.handler == sample_handler


# Teste com PathValidator
def test_path_validation_invalid(router: RouterAPI):
    with pytest.raises(PathValidationError):
        router.register_route("/api/{param1}/invalid-path", lambda _: None)


# Teste de tipos de entrada e saída
@pytest.mark.parametrize(
    "path,handler,expected_input_type",
    [
        ("/api/{param1}", str_arg_func, str),
        ("/api/", sample_handler_no_params, None),
    ],
)
def test_route_registration_type_hints(
    router: RouterAPI,
    path: str,
    handler: Callable[..., Any],
    expected_input_type: Any,
):
    router.register_route(path, handler)

    route_pack, _ = router.get_handler_pack(path)

    assert route_pack.input_type == expected_input_type
