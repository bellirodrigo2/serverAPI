from functools import partial
from typing import Any, Callable, Mapping, Optional, Union

from serveAPI.dependencies.mapfunction import FuncArg, get_func_args
from serveAPI.dependencies.model import Injectable


def resolve_val(
    key: str,
    arg: FuncArg,
    context: Mapping[Union[str, type], Any],
    raise_on_missing: bool,
    tgttype: type = Injectable,
) -> Optional[Any]:

    value = None
    instance: Injectable = arg.getinstance(tgttype)
    if key in context:
        value = context[key]
    elif type(instance) in context:
        value = context[type(instance)]
    elif instance.default is not Ellipsis:
        value = instance.default
    elif raise_on_missing:
        raise RuntimeError(f"Missing injectable for '{key}'")
    if value is not None:
        instance.validate(value)
    return value


def inject(
    func: Callable[..., Any],
    context: Mapping[Union[str, type], Any],
    raise_on_missing: bool,
    tgttype: type = Injectable,
):

    if not issubclass(tgttype, Injectable):
        raise TypeError(f'Cannot inject on {tgttype} args. Only on "Iinjectable"')
    args: dict[str, FuncArg] = {
        arg.name: arg for arg in get_func_args(func) if arg.hasinstance(tgttype)
    }
    resolved: dict[str, Any] = {}

    for key, arg in args.items():
        value = resolve_val(key, arg, context, raise_on_missing, tgttype)
        if value is not None:
            resolved[key] = value
    return partial(func, **resolved)
