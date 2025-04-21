import inspect
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, MutableMapping, Sequence, get_type_hints

from serveAPI.interfaces import IHandlerPack, IRouterAPI


class HandlerPack(IHandlerPack):

    def __init__(
        self,
        handler: Callable[..., Any],
        input_type: type | None,
        # output_type: type | None,
        params: tuple[str, ...],
    ):
        self._handler = handler
        self._input_type = input_type
        # self._output_type = output_type
        self._params = params

    @property
    def params(self) -> tuple[str, ...]:
        return self._params

    @property
    def handler(self) -> Callable[..., Any]:
        return self._handler

    @property
    def input_type(self) -> type | None:
        return self._input_type

    # @property
    # def output_type(self) -> type | None:
    # return self._output_type


class PathValidationError(ValueError):
    pass


@dataclass
class PathValidator:
    # _pattern: str = field(default=r"^[a-zA-Z0-9_\-/{}]+$") #com hifen
    _pattern: str = field(default=r"^[a-zA-Z0-9_/{}]+$")  # sem hifen

    def _compile(self):
        return re.compile(self._pattern)

    def validate_path(self, path: str, name: str = "path") -> None:
        path = path.strip()
        if not path:
            raise PathValidationError(f"{name} cannot be empty.")
        if not self._compile().fullmatch(path):
            raise PathValidationError(
                f"{name} '{path}' contains invalid characters. Allowed: a-zA-Z0-9_/{{}}"
            )


def extract_path_params(path: str) -> tuple[tuple[str, ...], str]:

    pattern = re.compile(r"{([^{}]+)}")
    params = tuple(pattern.findall(path))
    normalized = pattern.sub("{}", path)
    return params, f"/{normalized.strip('/')}/"


@dataclass
class RouterAPI(IRouterAPI):
    prefix: str
    routes: MutableMapping[str, IHandlerPack] = field(
        default_factory=dict[str, IHandlerPack]
    )
    path_validator: PathValidator = field(default_factory=PathValidator)

    # def __post_init__(self):
    # self.prefix = self.prefix.strip("/")

    def items(self) -> Sequence[tuple[str, IHandlerPack]]:
        return list(self.routes.items())

    def _make_fullpath(self, path: str) -> str:
        return f"/{path.strip('/')}/"

    def register_route(self, path: str, handler: Callable[..., Any]) -> None:

        self.path_validator.validate_path(path, name="path")

        type_hints = get_type_hints(handler)
        sig = inspect.signature(handler)

        param_list = list(sig.parameters.values())

        if not param_list:
            input_type = None
        else:
            input_type = type_hints.get(param_list[0].name, dict)

        # output_type = type_hints.get("return", Any)
        full_path = self._make_fullpath(path)

        params, normpath = extract_path_params(full_path)

        self.routes[normpath] = HandlerPack(
            handler=handler,
            input_type=input_type,
            # output_type=output_type,
            params=params,
        )

    def route(self, path: str):
        def decorator(handler: Callable[..., Any]):
            self.register_route(path, handler)
            return handler

        return decorator

    def get_handler_pack(self, route: str) -> tuple[IHandlerPack, Mapping[str, str]]:

        route = f"/{route.strip('/')}/"

        params_input, normroute = extract_path_params(route)

        if normroute in self.routes:
            route_pack = self.routes[normroute]
            params_key = route_pack.params

            if len(params_input) != len(params_key):
                raise Exception()

            params = dict(zip(params_key, params_input))

            return route_pack, params
        raise Exception


if __name__ == "__main__":

    def func():
        return 1

    sig = inspect.signature(func)
    param_list = list(sig.parameters.values())
    print(param_list)
