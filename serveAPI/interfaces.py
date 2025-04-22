from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Literal,
    Mapping,
    Protocol,
    Sequence,
    Type,
    TypeVar,
)

T = TypeVar("T")
# Tco = TypeVar("Tco", covariant=True)

middlewareType = Literal["request", "response"]


class IMiddleware(Protocol[T]):

    def add_middleware_func(
        self, func: Callable[[T], T], type: middlewareType
    ) -> Callable[[T], T]: ...
    def add_middleware(self, type: middlewareType) -> Callable[
        [Callable[[T], T]],
        Callable[[T], T],
    ]: ...
    def proc(self, data: T, type: middlewareType) -> T: ...


class IHandlerPack(Protocol):

    @property
    def params(self) -> tuple[str, ...]: ...
    @property
    def handler(self) -> Callable[..., Any]: ...
    @property
    def input_type(self) -> type | None: ...

    # @property
    # def output_type(self) -> type | None: ...


class IRouterAPI(Protocol):
    def items(self) -> Sequence[tuple[str, IHandlerPack]]: ...
    def register_route(self, path: str, handler: Callable[..., Any]) -> None: ...
    def route(self, path: str) -> Callable[..., Callable[..., Any]]: ...
    def get_handler_pack(
        self, route: str
    ) -> tuple[IHandlerPack, Mapping[str, str]]: ...


class Params(dict[str, str]):
    pass


class ISockerServer(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def write(self, data: bytes, addr: str | tuple[str, int]) -> None: ...


class ITaskRunner(Protocol):
    def inject_server(self, server: ISockerServer) -> None: ...
    async def execute(self, input: bytes, addr: str | tuple[str, int]) -> str: ...


class ValidatorFunc(Protocol):
    def __call__(self, arg: Any, type_: type[Any]) -> Any: ...


class LaunchTask(Protocol):
    def __call__(self, func: Callable[[], Any], cb: Callable[..., Any]) -> None: ...


class IDispatcher(Protocol):

    def inject_server(self, server: ISockerServer): ...

    async def dispatch(
        self,
        func: Callable[[], Any],
        addr: str | tuple[str, int],
    ) -> None: ...


class IExceptionRegistry(Protocol):

    def set_handler(
        self,
        exc_type: Type[BaseException],
        handler: Callable[[BaseException], Awaitable[Any]],
    ) -> None: ...

    def decorator(
        self,
        exc_type: Type[BaseException],
    ) -> Callable[
        [Callable[[BaseException], Coroutine[Any, Any, Any]]],
        Callable[[BaseException], Coroutine[Any, Any, Any]],
    ]: ...

    async def resolve(self, exc: BaseException) -> Any: ...


class IEncoder(Protocol[T]):
    def decode(self, input: bytes) -> tuple[str, T]: ...
    def encode(self, output: T) -> bytes: ...
