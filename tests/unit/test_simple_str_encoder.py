import pytest

from serveAPI.datatypes.str_input import (
    SimpleStrEncoder,
    make_str_simple_header,
    parse_str_simple_header,
)


# Teste para a função make_str_simple_header
@pytest.mark.parametrize(
    "value, route",
    [
        ("value1", "/api/route1"),
        ("value2", "/api/route2"),
        ("test_value", "/test/route"),
    ],
)
def test_make_str_simple_header(value, route):
    """Verifica a criação do header com id, route e value"""
    header = make_str_simple_header(value, route)

    # Verificar se o formato do header está correto
    assert header.startswith("serveAPI:")
    assert len(header.split(":")) == 3  # Deve ter 4 partes no header
    assert header.endswith(f"{route}:{value}")  # Deve terminar com route e value


# Teste para o parser parse_str_simple_header
@pytest.mark.parametrize(
    "header, expected_output",
    [
        ("serveAPI:/api/route1:value1", ("/api/route1", "value1")),
        ("serveAPI:/api/route2:value2", ("/api/route2", "value2")),
        (
            "serveAPI:/test/route:test_value",
            ("/test/route", "test_value"),
        ),
    ],
)
def test_parse_str_simple_header_valid(header, expected_output):
    """Verifica se o parser extrai corretamente id, route e value do header"""
    result = parse_str_simple_header(header)
    assert result == expected_output


# Teste para o comportamento do SimpleStrEncoder
@pytest.mark.parametrize(
    "value, route, expected_encoded, expected_decoded",
    [
        (
            "value1",
            "/api/route1",
            b"serveAPI:/api/route1:value1",
            "serveAPI:/api/route1:value1",
        ),
        (
            "value2",
            "/api/route2",
            b"serveAPI:/api/route2:value2",
            "serveAPI:/api/route2:value2",
        ),
        (
            "test_value",
            "/test/route",
            b"serveAPI:/test/route:test_value",
            "serveAPI:/test/route:test_value",
        ),
    ],
)
def test_intrusive_str_encoder(value, route, expected_encoded, expected_decoded):
    """Verifica a codificação e decodificação usando o SimpleStrEncoder"""

    encoder = SimpleStrEncoder()
    header = make_str_simple_header(value, route)
    encoded = encoder._encode(header)
    assert encoded == expected_encoded
    decoded = encoder._decode(encoded)
    assert decoded == expected_decoded


# Teste para o uso do parser dentro do encoder
@pytest.mark.parametrize(
    "header, expected_parsed",
    [
        ("serveAPI:/api/route1:value1", ("/api/route1", "value1")),
        ("serveAPI:/api/route2:value2", ("/api/route2", "value2")),
        (
            "serveAPI:/test/route:test_value",
            ("/test/route", "test_value"),
        ),
    ],
)
def test_parser_in_encoder(header, expected_parsed):
    """Verifica se o parser do encoder funciona corretamente ao extrair o id, route, e value"""

    encoder = SimpleStrEncoder()

    # Usar o parser do encoder
    parsed = encoder._parser(header)
    assert parsed == expected_parsed  # Verifica se o parsing está correto
