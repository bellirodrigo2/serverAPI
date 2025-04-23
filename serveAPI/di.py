import inspect
from dataclasses import dataclass, field
from typing import (
    Annotated,
    Any,
    Awaitable,
    Callable,
    MutableMapping,
    get_args,
    get_origin,
    get_type_hints,
)


@dataclass
class Depends:
    dependency: Callable[[], Any] | type[Any]  # <--- aqui está a mudança


@dataclass
class IoCContainer:
    _registry: dict[type[Any] | Callable[..., Any], Callable[["IoCContainer"], Any]] = (
        field(default_factory=dict)
    )

    def __setitem__(
        self, k: type[Any] | Callable[..., Any], v: Callable[["IoCContainer"], Any]
    ):
        self._registry[k] = v

    def __getitem__(self, k: type[Any] | Callable[..., Any]):
        return self._registry[k]

    def get(self, k: type[Any] | Callable[..., Any], default: Any | None = None):
        return self._registry.get(k, default)

    def __contains__(self, k: type[Any] | Callable[..., Any]) -> bool:
        return k in self._registry

    def register(
        self,
        type_: type[Any] | Callable[..., Any],
        provider: Callable[["IoCContainer"], Any],
    ) -> None:
        self._registry[type_] = provider

    def resolve(self, type_: type[Any] | Callable[..., Any]) -> Any:
        if type_ not in self._registry:
            raise ValueError(f"No provider registered for {type_}")

        instance = self._registry[type_](self)
        return instance


@dataclass
class IoCContainerSingleton(IoCContainer):
    _instances: MutableMapping[type[Any] | Callable[..., Any], Any] = field(
        default_factory=dict[type[Any] | Callable[..., Any], Any]
    )

    def resolve(self, type_: type[Any] | Callable[..., Any]) -> Any:
        if type_ in self._instances:
            return self._instances[type_]

        instance = super().resolve(type_)
        self._instances[type_] = instance
        return instance


@dataclass
class DependencyInjector:
    container: IoCContainer = field(default_factory=IoCContainer)

    async def resolve(self, func: Callable[..., Any]) -> MutableMapping[str, Any]:
        return await self._resolve_dependencies(func)

    async def _resolve_dependencies(
        self, func: Callable[..., Any]
    ) -> MutableMapping[str, Any]:
        sig = inspect.signature(func)
        type_hints = get_type_hints(func, include_extras=True)
        kwargs: MutableMapping[str, Any] = {}

        for name, param in sig.parameters.items():
            depends_obj: Depends | None = None

            # 1. Checar se é Annotated com Depends dentro
            annotation = type_hints.get(name)
            if annotation and get_origin(annotation) is Annotated:
                _, *extras = get_args(annotation)
                for extra in extras:
                    if isinstance(extra, Depends):
                        depends_obj = extra
                        break

            # 2. Se não for Annotated, checar se default é Depends
            if depends_obj is None and isinstance(param.default, Depends):
                depends_obj = param.default

            # 3. Se achou Depends, resolve
            if depends_obj:
                value = await self._resolve_single(depends_obj)
                kwargs[name] = value

        return kwargs

    async def _resolve_single(self, dep_obj: Depends) -> Any:
        dep = dep_obj.dependency

        if isinstance(dep, type):
            value = self.container.resolve(dep)
        else:
            # Resolve dependências da função de forma recursiva
            inner_kwargs = await self._resolve_dependencies(dep)
            value = dep(**inner_kwargs)

        if isinstance(value, Awaitable):
            value = await value

        return value


if __name__ == "__main__":
    ...
    # class MyService:
    #     def ping(self):
    #         return "pong"

    # container = IoCContainerSingleton()
    # container.register(MyService, lambda c: MyService())  # registra no IoC

    # injector = DependencyInjector(container=container)  # usa IoC direto

    # async def handler(service=Depends(MyService)):
    #     print(service.ping())

    # import asyncio

    # args = asyncio.run(injector.resolve(handler))
    # await handler(**args)  # prints: pong
