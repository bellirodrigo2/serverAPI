from dataclasses import dataclass, field
from typing import Callable

from serveAPI.datatypes.str_hash import check_hash, make_hash
from serveAPI.di import IoCContainer
from serveAPI.encoder import IntrusiveHeaderEncoder
from serveAPI.exceptions import ParseError
from serveAPI.middleware import Middleware

# --------- Simple str Msg ----------------------


# CLIENT SIDE CODE COMPATIBLE WITH THE SERVER PARSER
def make_str_simple_header(value: str, route: str) -> str:
    return f"serveAPI:{route}:{value}"


def parse_str_simple_header(value: str) -> tuple[str, str]:

    prefix = "serveAPI:"
    if not value.startswith(prefix):
        raise Exception("Invalid header")

    value = value[len(prefix) :]

    sep_idx = value.find(":")
    if sep_idx == -1:
        raise Exception("Invalid header format")

    route = value[:sep_idx]
    payload = value[sep_idx + 1 :]

    return route, payload


@dataclass
class SimpleStrEncoder(IntrusiveHeaderEncoder[str]):
    _encode: Callable[[str], bytes] = field(default=lambda x: x.encode())
    _decode: Callable[[bytes], str] = field(default=lambda x: x.decode())
    _parser: Callable[[str], tuple[str, str]] = field(default=parse_str_simple_header)


MiddlewareStr = Middleware[str]


def provide_str_simple_encoder(_: IoCContainer) -> SimpleStrEncoder:
    return SimpleStrEncoder()


def provide_str_middleware(_: IoCContainer) -> MiddlewareStr:
    return MiddlewareStr()


# --------- Hashed str Msg ----------------------


def make_str_hashed_header(value: str, route: str) -> str:

    hashed = make_hash(value)

    return f"serveAPI:{hashed}:{route}:{value}"


def parse_str_hashed_header(header: str) -> tuple[str, str]:
    prefix = "serveAPI:"
    if not header.startswith(prefix):
        raise Exception("Invalid prefix")

    start = len(prefix)

    # Primeiro separador depois do prefixo (fim do hash)
    hash_end = header.find(":", start)
    if hash_end == -1:
        raise ParseError(
            f"Function<parse_str_hashed_header>: Invalid format: hash_end == -1"
        )

    hashed = header[start:hash_end]

    # Próximo separador (fim da rota)
    route_end = header.find(":", hash_end + 1)
    if route_end == -1:
        raise ParseError(
            f"Function<parse_str_hashed_header>: Invalid format: route_end == -1"
        )

    route = header[hash_end + 1 : route_end]
    value = header[route_end + 1 :]

    if not check_hash(value, hashed):
        raise Exception("Hash mismatch")

    return route, value


@dataclass
class HashedStrEncoder(IntrusiveHeaderEncoder[str]):
    _encode: Callable[[str], bytes] = field(default=lambda x: x.encode())
    _decode: Callable[[bytes], str] = field(default=lambda x: x.decode())
    _parser: Callable[[str], tuple[str, str]] = field(default=parse_str_hashed_header)


def provide_str_hashed_encoder(_: IoCContainer) -> SimpleStrEncoder:
    return SimpleStrEncoder()
