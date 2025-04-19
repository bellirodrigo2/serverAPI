from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Awaitable, Coroutine, MutableMapping, Type

from serveAPI.interfaces import IExceptionRegistry


@dataclass
class ExceptionRegistry(IExceptionRegistry):
    _handlers: MutableMapping[
        Type[BaseException], Callable[[BaseException], Awaitable[Any]]
    ]

    def add_handler(
        self, exc_type: Type[BaseException]
    ) -> Callable[..., Callable[[BaseException], Awaitable[Any]]]:
        def decorator(func: Callable[[BaseException], Awaitable[Any]]):
            self._handlers[exc_type] = func
            return func

        return decorator

    def decorator(
        self, exc_type: Type[BaseException]
    ) -> Callable[..., Callable[[BaseException], Awaitable[Any]]]:
        def wrapper(func: Callable[[BaseException], Coroutine[Any, Any, Any]]):
            self._handlers[exc_type] = func
            return func

        return wrapper

    async def resolve(self, exc: BaseException) -> Any:
        for exc_type, handler in self._handlers.items():
            if isinstance(exc, exc_type):
                return await handler(exc)
        raise exc  # se não tiver handler, relança
