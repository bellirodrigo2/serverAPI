from dataclasses import dataclass
from typing import Any, Callable, MutableMapping, MutableSequence


@dataclass
class Middleware:

    procs: MutableSequence[
        Callable[[MutableMapping[str, Any]], MutableMapping[str, Any]]
    ]

    def add_middleware(self):
        def decorator(
            func: Callable[[MutableMapping[str, Any]], MutableMapping[str, Any]],
        ):
            self.procs.append(func)
            return func

        return decorator

    def proc(self, data: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        for proc in self.procs:
            data = proc(data)
        return data
