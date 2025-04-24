import inspect
from dataclasses import dataclass, field
from typing import (
    Annotated,
    Any,
    Awaitable,
    Callable,
    MutableMapping,
    Sequence,
    get_args,
    get_origin,
    get_type_hints,
)

from serveAPI.interfaces import Depends


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

    def _unwrap_annotation(self, annotation: Any) -> tuple[Any, Sequence[Any]]:
        if annotation is None:
            return None, ()
        origin = get_origin(annotation)
        if origin is None:
            return annotation, ()
        if origin is Annotated:
            args = get_args(annotation)
            return args[0], args[1:]
        return annotation, ()

    async def resolve(
        self,
        func: Callable[..., Any],
        context: MutableMapping[Any, Any] | None = None,
    ) -> MutableMapping[str, Any]:
        context = context or {}
        return await self._resolve_dependencies(func, context)

    async def _resolve_dependencies(
        self,
        func: Callable[..., Any],
        context: MutableMapping[Any, Any],
    ) -> MutableMapping[str, Any]:
        sig = inspect.signature(func)
        type_hints = get_type_hints(func, include_extras=True)
        kwargs: MutableMapping[str, Any] = {}

        for name, param in sig.parameters.items():
            annotation = type_hints.get(name)
            real_type, extras = self._unwrap_annotation(annotation)

            # 1) Injeção por contexto (Params, IAddr, etc)
            if real_type in context:
                kwargs[name] = context[real_type]
                continue

            # 2) Procura Depends em Annotated extras
            depends_obj: Depends | None = None
            for extra in extras:
                if isinstance(extra, Depends):
                    depends_obj = extra
                    break

            # 3) Se não achou em Annotated, vê se default é Depends
            if depends_obj is None and isinstance(param.default, Depends):
                depends_obj = param.default

            # 4) Se for Depends, resolve
            if depends_obj:
                value = await self._resolve_single(depends_obj, context)
                kwargs[name] = value
                continue

            # 5) Caso naked real_type seja um IO-container‐registered type
            if isinstance(real_type, type) and real_type in self.container:
                kwargs[name] = self.container.resolve(real_type)
                continue

            # Caso contrário, ignora (param obrigatório levantará TypeError quando chamar)
        return kwargs

    async def _resolve_single(
        self,
        dep_obj: Depends,
        context: MutableMapping[Any, Any],
    ) -> Any:
        dep = dep_obj.dependency

        if isinstance(dep, type):
            # resolve do IoC
            value = self.container.resolve(dep)
        else:
            # função: resolve recursivamente suas próprias deps
            inner_kwargs = await self._resolve_dependencies(dep, context)
            value = dep(**inner_kwargs)

        if isinstance(value, Awaitable):
            value = await value
        return value

    async def run_validate_dependencies(
        self,
        funcs: Sequence[Callable[..., Any]],
        context: MutableMapping[Any, Any] | None = None,
    ) -> None:
        context = context or {}
        for func in funcs:
            await self.resolve(func, context)
