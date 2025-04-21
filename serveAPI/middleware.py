from dataclasses import dataclass, field
from typing import Callable, MutableSequence, TypeVar

from serveAPI.interfaces import IMiddleware

T = TypeVar("T")


@dataclass
class Middleware(IMiddleware[T]):

    procs: MutableSequence[Callable[[T], T]] = field(
        default_factory=list[Callable[[T], T]]
    )

    def add_middleware_func(self, func: Callable[[T], T]) -> Callable[[T], T]:
        """Adiciona middleware diretamente"""
        self.procs.append(func)
        return func

    def add_middleware(self) -> Callable[[Callable[[T], T]], Callable[[T], T]]:
        """Usado como decorador: @middleware.use()"""
        return self.add_middleware_func

    def proc(self, data: T) -> T:
        for proc in self.procs:
            data = proc(data)
        return data
