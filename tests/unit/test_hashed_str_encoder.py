import pytest

from serveAPI.datatypes.str_input import (
    HashedStrEncoder,
    make_str_hashed_header,
    parse_str_hashed_header,
)


# Teste para a função make_str_hashed_header
@pytest.mark.parametrize(
    "value, route",
    [
        ("value1", "/api/route1"),
        ("value2", "/api/route2"),
        ("test_value", "/test/route"),
    ],
)
def test_make_str_hashed_header(value, route):
    """Verifica a criação do header com id, route e value"""
    header = make_str_hashed_header(value, route)

    # Verificar se o formato do header está correto
    assert header.startswith("serveAPI:")
    assert len(header.split(":")) == 4  # Deve ter 4 partes no header
    assert header.endswith(f"{route}:{value}")  # Deve terminar com route e value


# Teste para o parser parse_str_hashed_header
@pytest.mark.parametrize(
    "route, value",
    [
        ("/api/route1", "value1"),
        ("/api/route2", "value2"),
        ("/test/route", "test_value"),
    ],
)
def test_parse_str_hashed_header_valid(route: str, value: str):
    """Verifica se o parser extrai corretamente id, route e value do header"""

    msg = make_str_hashed_header(value, route)
    parsedroute, parsedvalue = parse_str_hashed_header(msg)
    assert route == parsedroute
    assert value == parsedvalue


# Teste para o comportamento do HashedStrEncoder
@pytest.mark.parametrize(
    "value, route",
    [
        (
            "value1",
            "/api/route1",
        ),
        (
            "value2",
            "/api/route2",
        ),
        (
            "test_value",
            "/test/route",
        ),
    ],
)
def test_intrusive_str_encoder(value: str, route: str):
    """Verifica a codificação e decodificação usando o HashedStrEncoder"""

    encoder = HashedStrEncoder()
    header = make_str_hashed_header(value, route)
    encoded = encoder._encode(header)
    decoded = encoder._decode(encoded)

    assert encoded.startswith(b"serveAPI:")
    assert encoded.endswith(f":{route}:{value}".encode())

    assert decoded.startswith("serveAPI:")
    assert decoded.endswith(f":{route}:{value}")


# Teste para o uso do parser dentro do encoder
@pytest.mark.parametrize(
    "value, route",
    [
        (
            "value1",
            "/api/route1",
        ),
        (
            "value2",
            "/api/route2",
        ),
        (
            "test_value",
            "/test/route",
        ),
    ],
)
def test_parser_in_encoder(value, route):
    """Verifica se o parser do encoder funciona corretamente ao extrair o id, route, e value"""

    encoder = HashedStrEncoder()

    # Usar o parser do encoder
    msg = make_str_hashed_header(value, route).encode()

    decroute, decvalue = encoder.decode(msg)

    assert value == decvalue
    assert route == decroute
