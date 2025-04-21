from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Awaitable, Coroutine, MutableMapping, Type

from serveAPI.interfaces import IExceptionRegistry


@dataclass
class ExceptionRegistry(IExceptionRegistry):
    _handlers: MutableMapping[
        Type[BaseException], Callable[[BaseException], Awaitable[Any]]
    ] = field(
        default_factory=dict[
            Type[BaseException], Callable[[BaseException], Awaitable[Any]]
        ]
    )

    def set_handler(
        self,
        exc_type: Type[BaseException],
        handler: Callable[[BaseException], Awaitable[Any]],
    ) -> None:
        """Registra diretamente um handler para um tipo de exceção."""
        self._handlers[exc_type] = handler

    def decorator(
        self,
        exc_type: Type[BaseException],
    ) -> Callable[
        [Callable[[BaseException], Coroutine[Any, Any, Any]]],
        Callable[[BaseException], Coroutine[Any, Any, Any]],
    ]:
        """Decorator para uso como @app.exception_handler(SomeException)."""

        def wrapper(
            func: Callable[[BaseException], Coroutine[Any, Any, Any]],
        ) -> Callable[[BaseException], Coroutine[Any, Any, Any]]:
            self._handlers[exc_type] = func
            return func

        return wrapper

    async def resolve(self, exc: BaseException) -> Any:
        """Resolve uma exceção usando o handler registrado."""
        sorted_handlers = sorted(
            self._handlers.items(), key=lambda item: -len(item[0].mro())
        )

        for exc_type, handler in sorted_handlers:
            if isinstance(exc, exc_type):
                return await handler(exc)

        raise exc
