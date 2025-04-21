from dataclasses import dataclass, field
from typing import Callable

from serveAPI.di import IoCContainer
from serveAPI.encoder import IntrusiveHeaderEncoder
from serveAPI.interfaces import ValidatorFunc
from serveAPI.middleware import Middleware


def make_str_intruside_header(value: str, route: str, id: str) -> str:
    return f"serveAPI:{id}:{route}:{value}"


def str_intrusive_header(value: str) -> tuple[str, str, str]:

    return_tuple = tuple(value.split(":", 3))
    if len(return_tuple) == 4:
        return return_tuple[1:]
    raise Exception()


@dataclass
class IntrusiveStrEncoder(IntrusiveHeaderEncoder[str]):
    _encode: Callable[[str], bytes] = field(default=lambda x: x.encode())
    _decode: Callable[[bytes], str] = field(default=lambda x: x.decode())
    _parser: Callable[[str], tuple[str, str, str]] = field(default=str_intrusive_header)


class StrValidator(ValidatorFunc):
    def __call__(self, input: str, _: type[str]) -> str:
        if isinstance(input, str):  # type: ignore
            return input
        raise TypeError(f'Input type is "{type(input)}", but a "str" is expected')


MiddlewareStr = Middleware[str]


def provide_str_intrusive_encoder(_: IoCContainer) -> IntrusiveStrEncoder:
    return IntrusiveStrEncoder()


def provide_str_middleware(_: IoCContainer) -> MiddlewareStr:
    return MiddlewareStr()


def provide_str_validator(_: IoCContainer) -> StrValidator:
    return StrValidator()
