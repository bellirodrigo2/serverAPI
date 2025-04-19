from typing import Any, Awaitable, Callable, MutableMapping, Protocol, Type, TypeVar


class IMiddleware(Protocol):
    def add_middleware(self): ...
    def proc(self, data: MutableMapping[str, Any]) -> MutableMapping[str, Any]: ...


class IMetaExtractor(Protocol):
    def extract(self, input: bytes) -> tuple[str, str, bytes]: ...


class IMsgParser(Protocol):

    def input(self, input: bytes) -> MutableMapping[str, Any]: ...
    def output(self, output: MutableMapping[str, Any]) -> bytes: ...


class IDispatcher(Protocol):
    async def dispatch(
        self, func: Callable[..., Any], data: Any, id: str, addr: str | tuple[str, int]
    ) -> None: ...


class IHandlerPack(Protocol):
    @property
    def handler(self) -> Callable[..., Any]: ...
    @property
    def input_type(self) -> type | None: ...
    @property
    def output_type(self) -> type | None: ...


class ISocketRouter(Protocol):
    def add_route(self, path: str) -> Callable[..., Callable[..., Any]]: ...
    def get_handler_pack(self, route: str) -> IHandlerPack: ...


T = TypeVar("T")


class ITypeValidator(Protocol):
    def validate_input(
        self,
        data: MutableMapping[str, Any],
        input_type: Type[T] | None,
    ) -> T | None: ...

    def validate_output(
        self, handler: Callable[..., Any], output_type: type | None
    ) -> None: ...


class IHandler(Protocol):
    def handle(self, route: str, input: bytes) -> tuple[Callable[..., Any], Any]: ...


class ITaskRunner(Protocol):

    async def execute(self, input: bytes, addr: Any) -> tuple[str, str]: ...


class ITaskContext(Protocol):
    async def push(self, id: str, addr: str) -> None: ...
    async def respond(
        self, id: str, addr: str | tuple[str, int] | None, data: bytes
    ) -> None: ...


class ISockerServer:
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
