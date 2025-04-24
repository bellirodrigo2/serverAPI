import inspect
from dataclasses import dataclass, field
from functools import partial
from typing import (
    Annotated,
    Any,
    Awaitable,
    Callable,
    Generic,
    MutableSequence,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

from serveAPI.interfaces import Depends, IMiddleware, IMiddlewareFunc, middlewareType

T = TypeVar("T")


@dataclass
class Middleware(IMiddleware[T]):
    procs_req: MutableSequence[Callable[[T], T]] = field(
        default_factory=list[Callable[[T], T]]
    )
    procs_resp: MutableSequence[Callable[[T], T]] = field(
        default_factory=list[Callable[[T], T]]
    )

    def add_middleware_func(
        self, func: Callable[[T], T], type: middlewareType
    ) -> Callable[[T], T]:
        """Adiciona middleware diretamente"""
        if type == "request":
            self.procs_req.append(func)
        elif type == "response":
            self.procs_resp.append(func)
        else:
            raise Exception(
                f'Middleware should be for "request" or "response". "{type}" is not supported'
            )
        return func

    def add_middleware(
        self, type: middlewareType
    ) -> Callable[[Callable[[T], T]], Callable[[T], T]]:
        """Usado como decorador: @middleware.use()"""
        return partial(self.add_middleware_func, type=type)

    async def proc(self, data: T, type: middlewareType) -> T:
        procs = self.procs_req if type == "request" else self.procs_resp
        if type == "request":
            procs = self.procs_req
        elif type == "response":
            procs = self.procs_resp
        else:
            raise Exception(
                f'Middleware processing be for "request" or "response". "{type}" is not supported'
            )

        for proc in procs:
            data = proc(data)
        return data


def validate_middleware_signature(middleware: Callable[..., Any]) -> None:
    sig = inspect.signature(middleware)
    params = list(sig.parameters.values())

    # Verificar que pelo menos 'input' e 'call_next' estão presentes
    if len(params) < 2:
        raise TypeError(
            f"Middleware '{middleware.__name__}' must have at least 'input' and 'call_next' parameters."
        )

    # Verificar se o primeiro parâmetro é 'input'
    if params[0].name != "input":
        raise TypeError(
            f"First parameter must be named 'input', got '{params[0].name}'"
        )

    # Verificar se 'call_next' está presente
    if "call_next" not in [p.name for p in params]:
        raise TypeError(
            f"Middleware '{middleware.__name__}' must include a 'call_next' parameter."
        )

    # Verificar se os parâmetros 'params' e 'addr' estão corretos
    for param in params:
        if param.name == "params" or param.name == "addr":
            continue  # Ok, são parâmetros opcionais

    # Validar os parâmetros adicionais
    for param in params:
        if param.name in {"input", "call_next", "params", "addr"}:
            continue

        # Obter o tipo do parâmetro
        annotation = get_type_hints(middleware).get(param.name, Any)
        origin = get_origin(annotation)

        # Verificar se é 'Depends' ou 'Annotated[Depends]'
        if not (
            annotation is Depends
            or (origin is Annotated and Depends in get_args(annotation))
        ):
            raise TypeError(
                f"""Middleware '{middleware.__name__}' has an invalid parameter '{param.name}'. 
                "Only 'Depends' or 'Annotated[Depends]' are allowed for additional parameters."""
            )


@dataclass
class Middleware2(Generic[T]):
    stack: list[IMiddlewareFunc[T]] = field(default_factory=list)

    def __iter__(self):
        """Iterador sobre os middlewares, no formato reverso (para processar da última para a primeira)"""
        return iter(reversed(self.stack))

    def add(self, middleware: IMiddlewareFunc[T]) -> IMiddlewareFunc[T]:
        """Adiciona middleware no estilo FastAPI"""
        validate_middleware_signature(middleware)
        self.stack.append(middleware)
        return middleware

    def use(self) -> Callable[[IMiddlewareFunc[T]], IMiddlewareFunc[T]]:
        """Usado como decorador"""
        return self.add
