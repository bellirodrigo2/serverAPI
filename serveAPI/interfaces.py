from dataclasses import dataclass
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Literal,
    Protocol,
    Sequence,
    Type,
    TypeVar,
)

T = TypeVar("T")

middlewareType = Literal["request", "response"]


class Params(dict[str, str]):
    pass


class IAddr(Protocol):
    @property
    def ip(self) -> str: ...

    @property
    def port(self) -> int: ...


class IMiddlewareFunc(Protocol[T]):
    async def __call__(
        self,
        input: T,
        params: Params,
        addr: IAddr,
        call_next: Callable[..., Awaitable[T]],
        **kwargs: Any,
    ) -> T: ...


class IMiddleware(Protocol[T]):
    def add_middleware_func(
        self, func: Callable[[T], T], type: middlewareType
    ) -> Callable[[T], T]: ...
    def add_middleware(self, type: middlewareType) -> Callable[
        [Callable[[T], T]],
        Callable[[T], T],
    ]: ...
    async def proc(self, data: T, type: middlewareType) -> T: ...


@dataclass
class Depends:
    dependency: Callable[[], Any] | type[Any]


class IHandlerPack(Protocol):
    @property
    def params(self) -> tuple[str, ...]: ...
    @property
    def handler(self) -> Callable[..., Any]: ...
    @property
    def input_type(self) -> type | None: ...
    @property
    def dependencies(self) -> Sequence[Callable[..., Any]]: ...

    # @property
    # def output_type(self) -> type | None: ...


class IRouterAPI(Protocol):
    def items(self) -> Sequence[tuple[str, IHandlerPack]]: ...
    def register_route(
        self,
        path: str,
        handler: Callable[..., Any],
        *,
        dependencies: list[Depends] | None = None,
    ) -> None: ...
    def route(self, path: str) -> Callable[..., Callable[..., Any]]: ...
    def get_handler_pack(self, route: str) -> tuple[IHandlerPack, Params]: ...


class ISockerServer(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def write(self, data: bytes, addr: IAddr) -> None: ...


class TypeCast(Protocol[T]):
    def to_model(self, arg: T, model: type | None) -> Any: ...
    def from_model(self, arg: Any) -> T: ...


class LaunchTask(Protocol):
    def __call__(self, coro: Coroutine[Any, Any, None]) -> None: ...


class ITaskRunner(Protocol):
    def inject_server(self, server: ISockerServer) -> None: ...
    def __call__(self, input: bytes, addr: IAddr) -> None: ...


class IExceptionRegistry(Protocol):

    def __contains__(self, key: Type[BaseException]) -> bool: ...

    def set_handler(
        self,
        exc_type: Type[BaseException],
        handler: Callable[[BaseException], str],
    ) -> None: ...

    def decorator(
        self,
        exc_type: Type[BaseException],
    ) -> Callable[
        [Callable[[BaseException], str]],
        Callable[[BaseException], str],
    ]: ...

    def resolve(self, exc: BaseException) -> str: ...


class IEncoder(Protocol[T]):
    def decode(self, input: bytes) -> tuple[str, T]: ...
    def encode(self, output: T) -> bytes: ...
