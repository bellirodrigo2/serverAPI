import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, MutableMapping, get_type_hints

from serveAPI.interfaces import IHandlerPack, ISocketRouter


class HandlerPack(IHandlerPack):

    def __init__(
        self,
        handler: Callable[..., Any],
        input_type: type | None,
        output_type: type | None,
    ):
        self._handler = handler
        self._input_type = input_type
        self._output_type = output_type

    @property
    def handler(self) -> Callable[..., Any]:
        return self._handler

    @property
    def input_type(self) -> type | None:
        return self._input_type

    @property
    def output_type(self) -> type | None:
        return self._output_type


@dataclass
class SocketRouter(ISocketRouter):
    prefix: str
    routes: MutableMapping[str, IHandlerPack] = field(
        default_factory=dict[str, IHandlerPack]
    )

    def register_route(self, path: str, handler: Callable[..., Any]) -> None:

        type_hints = get_type_hints(handler)
        sig = inspect.signature(handler)

        param_list = list(sig.parameters.values())
        if not param_list:
            input_type = None
        else:
            input_type = type_hints.get(param_list[0].name, dict)

        output_type = type_hints.get("return", Any)

        full_path = f"{self.prefix}/{path}"

        self.routes[full_path] = HandlerPack(
            handler=handler,
            input_type=input_type,
            output_type=output_type,
        )

    def add_route(self, path: str):
        def decorator(handler: Callable[..., Any]):
            self.register_route(path, handler)
            return handler

        return decorator

    def get_handler_pack(self, route: str) -> IHandlerPack:
        try:
            if route in self.routes:
                return self.routes[route]

            else:
                raise Exception(f"Route {route} not Found!")

        except Exception as e:
            raise e
