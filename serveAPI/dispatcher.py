from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Sequence

from serveAPI.interfaces import (
    IDispatcher,
    IExceptionRegistry,
    IMiddleware,
    IMsgParser,
    ITaskContext,
    ITypeValidator,
)


@dataclass
class Dispatcher(IDispatcher):
    validator: ITypeValidator
    parser: IMsgParser
    middleware: IMiddleware
    context: ITaskContext
    spawn: Callable[[Coroutine[Any, Any, Any]], None]
    exception_handlers: IExceptionRegistry

    async def dispatch(
        self,
        func: Callable[..., Any],
        data: Any,
        id: str,
        addr: str | tuple[str, int],
    ) -> None:

        self.spawn(self._run(func, data, id, addr))

    async def _run(
        self, func: Callable[..., Any], data: Any, id: str, addr: str | tuple[str, int]
    ) -> None:
        try:
            response = await func(data)
            self.validator.validate_output(func, type(response))

            response = self.middleware.proc(response)

            encoded = self.parser.output(response)

            await self.context.respond(id, addr, encoded)

        except Exception as e:
            try:
                result = await self.exception_handlers.resolve(e)
                encoded = self.parser.output(result)
                await self.context.respond(id, addr, encoded)
            except Exception as inner:
                # fallback, erro no handler ou sem handler
                await self.context.respond(
                    id, addr, f"Unhandled error: {str(inner)}".encode()
                )
