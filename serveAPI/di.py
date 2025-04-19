import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, MutableMapping


@dataclass
class Depends:
    dependency: Callable[[], Any]


async def resolve_dependencies(func: Callable[..., Any]) -> MutableMapping[str, Any]:
    sig = inspect.signature(func)
    kwargs: MutableMapping[str, Any] = {}

    for name, param in sig.parameters.items():
        default = param.default

        if isinstance(default, Depends):
            dep = default.dependency
            value = dep()
            if isinstance(value, Awaitable):
                value = await value
            kwargs[name] = value

    return kwargs
