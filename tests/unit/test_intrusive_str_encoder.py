import pytest

from serveAPI.input_types.str_input import (
    IntrusiveStrEncoder,
    make_str_intruside_header,
    str_intrusive_header,
)


# Teste para a função make_str_intruside_header
@pytest.mark.parametrize(
    "value, route",
    [
        ("value1", "/api/route1"),
        ("value2", "/api/route2"),
        ("test_value", "/test/route"),
    ],
)
def test_make_str_intruside_header(value, route):
    """Verifica a criação do header com id, route e value"""
    header = make_str_intruside_header(value, route, "id1")

    # Verificar se o formato do header está correto
    assert header.startswith("serveAPI:")
    assert len(header.split(":")) == 4  # Deve ter 4 partes no header
    assert header.endswith(f"{route}:{value}")  # Deve terminar com route e value

    # Verificar se o ID é um UUID válido
    assert len(header.split(":")[1]) == 3  # O UUID tem 36 caracteres


# Teste para o parser str_intrusive_header
@pytest.mark.parametrize(
    "header, expected_output",
    [
        ("serveAPI:12345:/api/route1:value1", ("12345", "/api/route1", "value1")),
        ("serveAPI:67890:/api/route2:value2", ("67890", "/api/route2", "value2")),
        (
            "serveAPI:abcdef:/test/route:test_value",
            ("abcdef", "/test/route", "test_value"),
        ),
    ],
)
def test_str_intrusive_header_valid(header, expected_output):
    """Verifica se o parser extrai corretamente id, route e value do header"""
    result = str_intrusive_header(header)
    assert result == expected_output


# Teste para o comportamento do IntrusiveStrEncoder
@pytest.mark.parametrize(
    "value, route, expected_encoded, expected_decoded",
    [
        (
            "value1",
            "/api/route1",
            b"serveAPI:id1:/api/route1:value1",
            "serveAPI:id1:/api/route1:value1",
        ),
        (
            "value2",
            "/api/route2",
            b"serveAPI:id1:/api/route2:value2",
            "serveAPI:id1:/api/route2:value2",
        ),
        (
            "test_value",
            "/test/route",
            b"serveAPI:id1:/test/route:test_value",
            "serveAPI:id1:/test/route:test_value",
        ),
    ],
)
def test_intrusive_str_encoder(value, route, expected_encoded, expected_decoded):
    """Verifica a codificação e decodificação usando o IntrusiveStrEncoder"""

    encoder = IntrusiveStrEncoder()
    header = make_str_intruside_header(value, route, id="id1")
    encoded = encoder._encode(header)
    assert encoded == expected_encoded
    decoded = encoder._decode(encoded)
    assert decoded == expected_decoded


# Teste para o uso do parser dentro do encoder
@pytest.mark.parametrize(
    "header, expected_parsed",
    [
        ("serveAPI:12345:/api/route1:value1", ("12345", "/api/route1", "value1")),
        ("serveAPI:67890:/api/route2:value2", ("67890", "/api/route2", "value2")),
        (
            "serveAPI:abcdef:/test/route:test_value",
            ("abcdef", "/test/route", "test_value"),
        ),
    ],
)
def test_parser_in_encoder(header, expected_parsed):
    """Verifica se o parser do encoder funciona corretamente ao extrair o id, route, e value"""

    encoder = IntrusiveStrEncoder()

    # Usar o parser do encoder
    parsed = encoder._parser(header)
    assert parsed == expected_parsed  # Verifica se o parsing está correto
