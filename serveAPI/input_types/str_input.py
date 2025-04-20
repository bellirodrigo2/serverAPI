from dataclasses import dataclass, field
from typing import Callable

from serveAPI.di import IoCContainer
from serveAPI.encoder import IntrusiveHeaderEncoder
from serveAPI.middleware import Middleware


def str_decode(value: bytes) -> str:
    return value.decode()


def str_encode(value: str) -> bytes:
    return value.encode()


def str_intrusive_header(value: str) -> tuple[str, str, str]:

    return_tuple = tuple(value.split(":"))
    if len(return_tuple) == 3:
        return return_tuple
    raise Exception()


@dataclass
class IntrusiveStrEncoder(IntrusiveHeaderEncoder[str]):
    _encode: Callable[[str], bytes] = field(default=str_encode)
    _decode: Callable[[bytes], str] = field(default=str_decode)
    _parser: Callable[[str], tuple[str, str, str]] = field(default=str_intrusive_header)


def str_validator(input: str, _: type) -> str:
    if isinstance(input, str):  # type: ignore
        return input
    raise TypeError(f'Input type is "{type(input)}", but a "str" is expected')


MiddlewareStr = Middleware[str]


def provide_str_intrusive_encoder(_: IoCContainer) -> IntrusiveStrEncoder:
    return IntrusiveStrEncoder()


def provide_str_middleware(_: IoCContainer) -> MiddlewareStr:
    return MiddlewareStr()
