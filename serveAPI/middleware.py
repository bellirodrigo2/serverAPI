from dataclasses import dataclass, field
from functools import partial
from typing import Callable, MutableSequence, TypeVar

from serveAPI.interfaces import IMiddleware, middlewareType

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

    def proc(self, data: T, type: middlewareType) -> T:
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
