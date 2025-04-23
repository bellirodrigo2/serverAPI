from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, TypeVar

import orjson
from pydantic import BaseModel

from serveAPI.encoder import IntrusiveHeaderEncoder, NonIntrusiveHeaderEncoder
from serveAPI.exceptions import ParseError
from serveAPI.interfaces import TypeCast


def dict_encode(value: Mapping[Any, Any]) -> bytes:
    return orjson.dumps(value)


def dict_decode(input: bytes) -> Mapping[Any, Any]:
    return orjson.loads(input)


# CLIENT SIDE CODE COMPATIBLE WITH THE SERVER PARSER
# at least 2 data copy involved
def make_nonintrusive_json_header(value: BaseModel, route: str) -> bytes:
    model_bytes = orjson.dumps(value.model_dump())
    header_prefix = f"serveAPI:{route}:".encode()
    return header_prefix + model_bytes


def parse_nonintrusive_json_header(value: bytes) -> tuple[str, bytes]:
    prefix = b"serveAPI:"
    if not value.startswith(prefix):
        raise ParseError(
            "Function<parse_nonintrusive_json_header>: Invalid Header: no prefix 'serveAPI:'"
        )

    route_start_idx = len(prefix)
    route_end_idx = value.find(b":", route_start_idx)

    if route_end_idx == -1:
        raise ParseError(
            "Function<parse_nonintrusive_json_header>: Invalid Header: no route separator ':'"
        )

    try:
        route = value[route_start_idx:route_end_idx].decode("utf-8")
    except UnicodeDecodeError:
        raise ParseError(
            "Function<parse_nonintrusive_json_header>: Route UTF-8 decode Fail"
        )

    modelinbytes = value[route_end_idx + 1 :]

    if not modelinbytes:
        raise ParseError("Function<parse_nonintrusive_json_header>: No msg data")

    return route, modelinbytes


def parse_intrusive_json_header(
    value: Mapping[Any, Any],
) -> tuple[str, Mapping[Any, Any]]:

    idx = "_route"
    if idx not in value:
        raise ParseError(
            f'Function<parse_intrusive_json_header>: Input dict has no field "{idx}"'
        )
    return value[idx], value


@dataclass
class IntrusiveMappingEncoder(IntrusiveHeaderEncoder[Mapping[str, Any]]):
    _encode: Callable[[Mapping[str, Any]], bytes] = field(default=dict_encode)
    _decode: Callable[[bytes], Mapping[str, Any]] = field(default=dict_decode)
    _parser: Callable[[Mapping[str, Any]], tuple[str, Mapping[str, Any]]] = field(
        default=parse_intrusive_json_header
    )


@dataclass
class NonIntrusiveMappingEncoder(NonIntrusiveHeaderEncoder[Mapping[str, Any]]):
    _encode: Callable[[Mapping[str, Any]], bytes] = field(default=dict_encode)
    _decode: Callable[[bytes], Mapping[str, Any]] = field(default=dict_decode)
    _parser: Callable[[bytes], tuple[str, bytes]] = field(
        default=parse_nonintrusive_json_header
    )


U = TypeVar("U")


class PydanticCast(TypeCast[Mapping[str, Any]]):
    def to_model(
        self,
        arg: Mapping[str, Any],
        model: Callable[..., U],
    ) -> U:
        return model(**arg)

    def from_model(self, arg: BaseModel) -> Mapping[str, Any]:
        return arg.model_dump()
