import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, MutableMapping, TypeVar


@dataclass
class Depends:
    # dependency: Callable[[], Any]
    dependency: Callable[[], Any] | type[Any]  # <--- aqui está a mudança


T = TypeVar("T")


@dataclass
class IoCContainer:

    _registry: dict[type[Any], Callable[["IoCContainer"], Any]] = field(
        default_factory=dict
    )

    def __setitem__(self, k: type[Any], v: Callable[["IoCContainer"], Any]):
        self._registry[k] = v

    def __getitem__(self, k: type[Any]):
        return self._registry[k]

    def get(self, k: type[Any], default: Any | None = None):
        return self._registry.get(k, default)

    def __contains__(self, k: type[Any]) -> bool:
        return k in self._registry

    def register(self, type_: type[T], provider: Callable[["IoCContainer"], T]) -> None:
        self._registry[type_] = provider

    def resolve(self, type_: type[T]) -> T:

        if type_ not in self._registry:
            raise ValueError(f"No provider registered for {type_}")

        instance = self._registry[type_](self)
        return instance


@dataclass
class IoCContainerInstance(IoCContainer):
    _instances: dict[type[Any], Any] = field(default_factory=dict)

    def resolve(self, type_: type[T]) -> T:
        if type_ in self._instances:
            return self._instances[type_]

        instance = super().resolve(type_)
        self._instances[type_] = instance
        return instance


@dataclass
class DependencyInjector:
    container: IoCContainer = field(default_factory=IoCContainer)

    async def resolve(self, func: Callable[..., Any]) -> MutableMapping[str, Any]:

        sig = inspect.signature(func)
        kwargs: MutableMapping[str, Any] = {}

        for name, param in sig.parameters.items():
            default = param.default

            if isinstance(default, Depends):
                dep = default.dependency

                if isinstance(dep, type):
                    value = self.container.resolve(dep)
                else:
                    dep = self.container.get(dep, dep)
                    value = dep()

                if isinstance(value, Awaitable):
                    value = await value
                kwargs[name] = value

        return kwargs


if __name__ == "__main__":

    class MyService:
        def ping(self):
            return "pong"

    container = IoCContainerInstance()
    container.register(MyService, lambda c: MyService())  # registra no IoC

    injector = DependencyInjector(container=container)  # usa IoC direto

    async def handler(service=Depends(MyService)):
        print(service.ping())

    import asyncio

    args = asyncio.run(injector.resolve(handler))
    await handler(**args)  # prints: pong
