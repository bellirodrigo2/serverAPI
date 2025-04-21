import inspect
import re
from dataclasses import dataclass, field
from typing import Any, Callable, MutableMapping, Sequence, get_type_hints

from serveAPI.interfaces import IHandlerPack, IRouterAPI


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


class PathValidationError(ValueError):
    pass


@dataclass
class PathValidator:
    # _pattern: str = field(default=r"^[a-zA-Z0-9_\-]+$")
    _pattern: str = field(default=r"^[a-zA-Z0-9_\-{}]+$")

    def _compile(self):
        return re.compile(self._pattern)

    def validate_path_segment(self, segment: str, name: str = "path") -> str:
        segment = segment.strip("/")
        if not segment:
            raise PathValidationError(f"{name} segment cannot be empty.")
        if "/" in segment:
            raise PathValidationError(
                f"{name} segment must not contain '/' characters."
            )
        if not self._compile().fullmatch(segment):
            raise PathValidationError(
                f"{name} segment '{segment}' contains invalid characters."
            )
        return segment


def extract_path_params(path: str) -> tuple[tuple[str, ...], str]:

    pattern = re.compile(r"{([^{}]+)}")
    params = tuple(pattern.findall(path))
    normalized = pattern.sub("{}", path)
    return params, normalized


@dataclass
class RouterAPI(IRouterAPI):
    prefix: str = field(default="")
    routes: MutableMapping[str, IHandlerPack] = field(
        default_factory=dict[str, IHandlerPack]
    )
    path_validator: PathValidator = field(default_factory=PathValidator)

    # def __post_init__(self):
    # self.prefix = self.prefix.strip("/")

    def items(self) -> Sequence[tuple[str, IHandlerPack]]:
        return list(self.routes.items())

    def _make_fullpath(self, path: str) -> str:
        try:
            cleaned_path = self.path_validator.validate_path_segment(path, name="path")
            if self.prefix:
                cleaned_prefix = self.path_validator.validate_path_segment(
                    self.prefix, name="prefix"
                )
                return f"/{cleaned_prefix}/{cleaned_path}"
            return f"/{cleaned_path}"
        except PathValidationError as e:
            raise ValueError(f"Invalid path construction: {e}")

    def register_route(self, path: str, handler: Callable[..., Any]) -> None:

        type_hints = get_type_hints(handler)
        sig = inspect.signature(handler)

        param_list = list(sig.parameters.values())
        if not param_list:
            input_type = None
        else:
            input_type = type_hints.get(param_list[0].name, dict)

        output_type = type_hints.get("return", Any)
        full_path = self._make_fullpath(path)

        self.routes[full_path] = HandlerPack(
            handler=handler,
            input_type=input_type,
            output_type=output_type,
        )

    def route(self, path: str):
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
