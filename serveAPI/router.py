import inspect
import re
from dataclasses import dataclass, field
from typing import (
    Annotated,
    Any,
    Callable,
    Generic,
    MutableMapping,
    Sequence,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

from serveAPI.di import Depends
from serveAPI.interfaces import IAddr, IHandlerPack, IRouterAPI, Params

T = TypeVar("T")


@dataclass(frozen=True)
class HandlerPack:
    handler: Callable[..., Any]
    input_type: type | None
    # output_type: type | None
    params: tuple[str, ...]
    dependencies: list[Callable[..., Any]] = field(default_factory=list)

    # def __str__(self) -> str:
    # return f'HandlerPack(input_type:"{self.input_type}, params:"{self.params}"")'


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


def validate_handler_signature(handler: Callable[..., Any]) -> type:
    """
    Valida se o handler tem:
    - Exatamente 1 argumento de tipo qualquer (entrada principal)
    - 0 ou 1 Params
    - 0 ou 1 IAddr
    - Quantos Depends quiser (inclusive em Annotated)

    Retorna o tipo de entrada principal (modelo), se válido.
    """
    type_hints = get_type_hints(handler, include_extras=True)
    sig = inspect.signature(handler)
    param_list = list(sig.parameters.values())

    count_main = 0
    count_params = 0
    count_addr = 0
    body_type: type | None = None

    for param in param_list:
        annotation = type_hints.get(param.name, Any)
        origin = get_origin(annotation)
        unwrapped = get_args(annotation)[0] if origin is Annotated else annotation

        if unwrapped is Params:
            count_params += 1
        elif unwrapped is IAddr:
            count_addr += 1
        elif isinstance(param.default, Depends):
            continue
        elif origin is Annotated:
            _, *extras = get_args(annotation)
            if any(isinstance(extra, Depends) for extra in extras):
                continue
            # Se não for Depends, é o tipo de entrada principal
            count_main += 1
            body_type = unwrapped
        else:
            # Assume como tipo de entrada principal
            count_main += 1
            body_type = unwrapped

    if count_main != 1:
        raise TypeError(
            f"Handler '{handler.__name__}' must have exactly one input argument (model)"
        )
    if count_params > 1:
        raise TypeError(
            f"Handler '{handler.__name__}' can have at most one Params parameter"
        )
    if count_addr > 1:
        raise TypeError(
            f"Handler '{handler.__name__}' can have at most one IAddr parameter"
        )

    return body_type or dict


@dataclass
class RouterAPI(IRouterAPI, Generic[T]):
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
        return f"/{path.strip('/')}/"

    def register_route(
        self,
        path: str,
        handler: Callable[..., Any],
        *,
        dependencies: list[Depends] | None = None,
    ) -> None:

        self.path_validator.validate_path(path, name="path")
        input_type = validate_handler_signature(handler)
        full_path = self._make_fullpath(path)
        params, normpath = extract_path_params(full_path)

        dependencies = dependencies or []
        self.routes[normpath] = HandlerPack(
            handler=handler,
            input_type=input_type,
            params=params,
            dependencies=[dep.dependency for dep in dependencies],
        )

    def route(self, path: str, *, dependencies: list[Depends] | None = None):
        def decorator(handler: Callable[..., Any]):
            self.register_route(path, handler, dependencies=dependencies)
            return handler

        return decorator

    def get_handler_pack(self, route: str) -> tuple[IHandlerPack, Params]:
        route = f"/{route.strip('/')}/"

        params_input, normroute = extract_path_params(route)

        if normroute in self.routes:
            route_pack = self.routes[normroute]
            params_key = route_pack.params

            if len(params_input) != len(params_key):
                raise Exception()

            params = Params(zip(params_key, params_input))

            return route_pack, params
        raise Exception(f"Route {route} not found on RouterAPI")


if __name__ == "__main__":

    def func():
        return 1

    sig = inspect.signature(func)
    param_list = list(sig.parameters.values())
    print(param_list)
