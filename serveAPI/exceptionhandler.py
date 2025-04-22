from collections.abc import Callable
from dataclasses import dataclass, field
from typing import MutableMapping, Type

from serveAPI.exceptions import UnhandledError
from serveAPI.interfaces import IExceptionRegistry


@dataclass
class ExceptionRegistry(IExceptionRegistry):
    _handlers: MutableMapping[Type[BaseException], Callable[[BaseException], str]] = (
        field(default_factory=dict[Type[BaseException], Callable[[BaseException], str]])
    )

    def set_handler(
        self,
        exc_type: Type[BaseException],
        handler: Callable[[BaseException], str],
    ) -> None:
        """Registra diretamente um handler para um tipo de exceção."""
        self._handlers[exc_type] = handler

    def decorator(
        self,
        exc_type: Type[BaseException],
    ) -> Callable[
        [Callable[[BaseException], str]],
        Callable[[BaseException], str],
    ]:
        """Decorator para uso como @app.exception_handler(SomeException)."""

        def wrapper(
            func: Callable[[BaseException], str],
        ) -> Callable[[BaseException], str]:
            self._handlers[exc_type] = func
            return func

        return wrapper

    def resolve(self, exc: BaseException) -> str:
        """Resolve uma exceção usando o handler registrado."""
        sorted_handlers = sorted(
            self._handlers.items(), key=lambda item: -len(item[0].mro())
        )

        for exc_type, handler in sorted_handlers:
            if isinstance(exc, exc_type):
                return handler(exc)

        raise UnhandledError() from exc
