import inspect
from dataclasses import dataclass
from functools import partial
from typing import (
    Annotated,
    Any,
    Callable,
    MutableMapping,
    Optional,
    Sequence,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)


class _NoDefault:
    def __repr__(self):
        return "NO_DEFAULT"

    def __str__(self):
        return "NO_DEFAULT"


NO_DEFAULT = _NoDefault()

T = TypeVar("T")


@dataclass
class FuncArg:
    name: str
    argtype: Optional[type]
    basetype: Optional[type]
    default: Optional[Any]
    extras: Optional[Sequence[Any]] = None

    def istype(self, tgttype: type) -> bool:
        return self.basetype == tgttype

    def getinstance(self, tgttype: type[T]) -> T:
        if self.default is not None and isinstance(self.default, tgttype):
            return self.default
        if self.extras is not None:
            founds = [e for e in self.extras if isinstance(e, tgttype)]
            if len(founds) > 0:
                return founds[0]
        return None

    def hasinstance(self, tgttype: type):
        if self.default is not None and isinstance(self.default, tgttype):
            return True
        if self.extras is not None:
            founds = [e for e in self.extras if isinstance(e, tgttype)]
            if len(founds) > 0:
                return True
        return False


def get_func_args(func: Callable[..., Any]) -> Sequence[FuncArg]:
    partial_args = {}
    if isinstance(func, partial):
        partial_args = func.keywords or {}
        func = func.func

    sig = inspect.signature(func)
    hints = get_type_hints(func, include_extras=True)
    funcargs: list[FuncArg] = []

    for name, param in sig.parameters.items():
        if name in partial_args:
            continue  # já foi resolvido via partial, ignora

        annotation: type = hints.get(name, param.annotation)
        default = param.default if param.default is not inspect._empty else NO_DEFAULT  # type: ignore

        argtype = (
            annotation
            if annotation is not inspect._empty  # type: ignore
            else (type(default) if default not in [NO_DEFAULT, None] else None)
        )
        basetype = argtype
        arg = FuncArg(name=name, argtype=argtype, basetype=basetype, default=default)
        if get_origin(annotation) is Annotated:
            base_type, *extras = get_args(annotation)
            arg.basetype = base_type
            arg.extras = extras
        funcargs.append(arg)
    return funcargs


def map_types(
    func: Callable[..., Any],
    tgttype: type,
) -> MutableMapping[str, Any]:

    func_args = get_func_args(func)
    mapped_args: dict[str, Any] = {}
    for arg in func_args:

        instance = arg.getinstance(tgttype)
        if instance:
            mapped_args[arg.name] = instance
    return mapped_args
