from typing import (
    Any,
    Awaitable,
    Callable,
    MutableMapping,
    Protocol,
    Sequence,
    Type,
    TypeVar,
)

T = TypeVar("T")
# Tco = TypeVar("Tco", covariant=True)


class IMiddleware(Protocol[T]):
    def add_middleware(
        self,
    ) -> Callable[
        [Callable[[T], T]],
        Callable[[T], T],
    ]: ...
    def proc(self, data: T) -> T: ...


# class IMetaExtractor(Protocol):
# def extract(self, input: bytes) -> tuple[str, str, bytes]: ...


# class IMsgParser(Protocol):

# def input(self, input: bytes) -> MutableMapping[str, Any]: ...
# def output(self, output: MutableMapping[str, Any]) -> bytes: ...


class IDispatcher(Protocol):

    async def respond(
        self,
        id: str,
        addr: str | tuple[str, int] | None,
        data: bytes,
    ) -> None: ...
    async def dispatch(
        self,
        func: Callable[..., Any],
        data: Any,
        id: str,
        addr: str | tuple[str, int],
    ) -> None: ...


class IHandlerPack(Protocol):
    @property
    def handler(self) -> Callable[..., Any]: ...
    @property
    def input_type(self) -> type | None: ...
    @property
    def output_type(self) -> type | None: ...


class IRouterAPI(Protocol):
    def items(self) -> Sequence[tuple[str, IHandlerPack]]: ...
    def register_route(self, path: str, handler: Callable[..., Any]) -> None: ...
    def add_route(self, path: str) -> Callable[..., Callable[..., Any]]: ...
    def get_handler_pack(self, route: str) -> IHandlerPack: ...


class ITypeValidator(Protocol):
    def validate_input(
        self,
        data: MutableMapping[str, Any],
        input_type: Type[T] | None,
    ) -> T | None: ...

    def validate_output(
        self, handler: Callable[..., Any], output_type: type | None
    ) -> None: ...


class ITaskRunner(Protocol[T]):
    @property
    def routers(self) -> IRouterAPI: ...
    @property
    def middlewares(self) -> IMiddleware[T]: ...

    @property
    def overrides(
        self,
    ) -> MutableMapping[Callable[..., Any], Callable[..., Any]]: ...

    async def execute(self, input: bytes, addr: Any) -> tuple[str, str]: ...


class ISockerServer(Protocol):
    async def start(self) -> None: ...
    async def write(self, data: bytes, addr: str | tuple[str, int]) -> None: ...


class IExceptionRegistry(Protocol):

    def add_handler(
        self, exc_type: Type[BaseException]
    ) -> Callable[..., Callable[[BaseException], Awaitable[Any]]]: ...
    def decorator(
        self, exc_type: Type[BaseException]
    ) -> Callable[..., Callable[[BaseException], Awaitable[Any]]]: ...
    async def resolve(self, exc: BaseException) -> Any: ...


class IEncoder(Protocol[T]):
    def decode(self, input: bytes) -> tuple[str, str, T]: ...
    def encode(self, output: T) -> bytes: ...
