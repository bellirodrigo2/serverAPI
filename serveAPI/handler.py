from dataclasses import dataclass
from typing import Any, Callable, Sequence

from serveAPI.interfaces import (
    IHandler,
    IMiddleware,
    IMsgParser,
    ISocketRouter,
    ITypeValidator,
)


@dataclass
class Handler(IHandler):
    parser: IMsgParser
    router: ISocketRouter
    validator: ITypeValidator
    middleware: IMiddleware

    def handle(self, route: str, input: bytes) -> tuple[Callable[..., Any], Any]:

        data = self.parser.input(input)

        route_pack = self.router.get_handler_pack(route)
        handler = route_pack.handler

        data = self.middleware.proc(data)

        obj_data = self.validator.validate_input(data, route_pack.input_type)  # type: ignore

        return handler, obj_data
