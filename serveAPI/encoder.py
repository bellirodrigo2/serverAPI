from dataclasses import dataclass
from typing import Callable, TypeVar

from serveAPI.interfaces import IEncoder

T = TypeVar("T")


@dataclass
class BaseEncoder(IEncoder[T]):
    _encode: Callable[[T], bytes]
    _decode: Callable[[bytes], T]

    def decode(self, input: bytes) -> tuple[str, T]:
        raise Exception("Base Encoder has no implementation")

    def encode(self, output: T) -> bytes:
        return self._encode(output)


@dataclass
class IntrusiveHeaderEncoder(BaseEncoder[T]):
    _parser: Callable[[T], tuple[str, T]]

    def decode(self, input: bytes) -> tuple[str, T]:
        decoded = self._decode(input)

        return self._parser(decoded)


@dataclass
class NonIntrusiveHeaderEncoder(BaseEncoder[T]):
    _parser: Callable[[bytes], tuple[str, bytes]]

    def decode(self, input: bytes) -> tuple[str, T]:

        route, raw_data = self._parser(input)
        data = self._decode(raw_data)

        return route, data
