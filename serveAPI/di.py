import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, MutableMapping


@dataclass
class Depends:
    dependency: Callable[[], Any]


# @dataclass
# class DependencyInjector:
#     _overrides: MutableMapping[Callable[..., Any], Callable[..., Any]] = field(
#         default_factory=dict[Callable[..., Any], Callable[..., Any]]
#     )

#     def override(self, original: Callable[..., Any], replacement: Callable[..., Any]):
#         self._overrides[original] = replacement

#     def clear_overrides(self):
#         self._overrides.clear()

#     async def resolve(self, func: Callable[..., Any]) -> MutableMapping[str, Any]:
#         sig = inspect.signature(func)
#         kwargs: MutableMapping[str, Any] = {}

#         for name, param in sig.parameters.items():
#             default = param.default

#             if isinstance(default, Depends):
#                 dep = default.dependency
#                 dep = self._overrides.get(dep, dep)  # check for override
#                 value = dep()
#                 if isinstance(value, Awaitable):
#                     value = await value
#                 kwargs[name] = value

#         return kwargs


# ------------------ OUTRA OPCAO
@dataclass
class DependencyInjector:
    overrides: MutableMapping[Callable[..., Any], Callable[..., Any]] = field(
        default_factory=dict[Callable[..., Any], Callable[..., Any]]
    )

    async def resolve(self, func: Callable[..., Any]) -> MutableMapping[str, Any]:
        sig = inspect.signature(func)
        kwargs: MutableMapping[str, Any] = {}

        for name, param in sig.parameters.items():
            default = param.default

            if isinstance(default, Depends):
                dep = default.dependency
                dep = self._overrides.get(dep, dep)  # pega override se houver
                value = dep()
                if isinstance(value, Awaitable):
                    value = await value
                kwargs[name] = value

        return kwargs
